"""
Data Cleaning orchestrator service logic.
"""
import os
import math
import hashlib
from typing import List, Tuple, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

import pandas as pd
from app.core.config import settings

from app.common.enums import DatasetStatus
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.cleaning_job import CleaningJob
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.repositories.cleaning_job import CleaningJobRepository
from app.storage.local import LocalStorageService
from app.cleaning.engine import DataCleaningEngine
from app.services.profiling import ProfilingService
from app.importing.parsers.csv import CSVParser
from app.importing.parsers.excel import ExcelParser


class CleaningService:
    """
    Service managing dataset cleaning preview runs and versioned execution.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.cleaning_repo = CleaningJobRepository(session)
        self.engine = DataCleaningEngine()

    def _sanitize_sample(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Replaces NaN/Inf values with None to prevent JSON serialization errors."""
        for rec in records:
            for k, v in rec.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    rec[k] = None
        return records

    async def _load_active_dataframe(self, dataset: Dataset) -> Tuple[DatasetVersion, pd.DataFrame, str]:
        """Loads active version file from disk into Pandas DataFrame."""
        version = next((v for v in dataset.versions if v.is_current), None)
        if not version:
            raise BadRequestException("Dataset contains no active version to clean")

        local_path = version.storage_path.replace("local://", "", 1)
        ext = os.path.splitext(version.storage_path)[1].lower()

        parser = CSVParser() if ext == ".csv" else ExcelParser()
        df = parser.parse(local_path)
        return version, df, ext

    async def preview_cleaning(self, dataset_id: UUID, user_id: UUID, operations: List[dict]) -> dict:
        """
        Executes cleaning sequence in-memory. Performs zero database or disk writes.
        """
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        _, df, _ = await self._load_active_dataframe(dataset)
        
        # Run engine
        cleaned_df, summary, _ = self.engine.clean_dataframe(df, operations)
        
        # Warnings detection
        warnings = []
        for column in cleaned_df.columns:
            if cleaned_df[column].isna().all():
                warnings.append(f"Column '{column}' has become entirely null after operations.")

        before_stats = {
            "rows_count": len(df),
            "columns_count": len(df.columns),
            "missing_values": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum())
        }

        after_stats = {
            "rows_count": len(cleaned_df),
            "columns_count": len(cleaned_df.columns),
            "missing_values": int(cleaned_df.isna().sum().sum()),
            "duplicate_rows": int(cleaned_df.duplicated().sum())
        }

        return {
            "before": before_stats,
            "after": after_stats,
            "changes": summary,
            "warnings": warnings,
            "original_sample": self._sanitize_sample(df.head(10).to_dict(orient="records")),
            "cleaned_sample": self._sanitize_sample(cleaned_df.head(10).to_dict(orient="records"))
        }

    async def apply_cleaning(self, dataset_id: UUID, user_id: UUID, operations: List[dict]) -> Dataset:
        """
        Applies cleaning rules, writes cleaned file, disables old version active flag,
        creates new DatasetVersion, logs CleaningJob, and triggers auto-profiling.
        """
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        active_version, df, ext = await self._load_active_dataframe(dataset)
        
        # Execute operations
        cleaned_df, summary, execution_time_ms = self.engine.clean_dataframe(df, operations)
        
        # Generate target version details
        next_version = active_version.version_number + 1
        user_dir = os.path.join(settings.STORAGE_ROOT, "cleaned", str(user_id), str(dataset_id))
        os.makedirs(user_dir, exist_ok=True)
        
        filename = f"version_{next_version}{ext}"
        local_path = os.path.join(user_dir, filename)
        
        # Write to local file
        try:
            if ext == ".csv":
                cleaned_df.to_csv(local_path, index=False, encoding="utf-8")
            else:
                cleaned_df.to_excel(local_path, index=False, engine="openpyxl")
        except Exception as e:
            raise BadRequestException(f"Failed to write cleaned file to disk: {str(e)}")
            
        # Calculate checksum and size of new file
        sha256_hash = hashlib.sha256()
        with open(local_path, "rb") as f:
            while chunk := f.read(8192):
                sha256_hash.update(chunk)
                
        checksum = sha256_hash.hexdigest()
        file_size = os.path.getsize(local_path)
        normalized_path = local_path.replace("\\", "/")
        storage_path = f"local://{normalized_path}"
        
        # Update database transaction
        try:
            # 1. Deactivate old version
            await self.version_repo.update(active_version, {"is_current": False})
            
            # 2. Add new version
            new_version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset_id,
                version_number=next_version,
                storage_path=storage_path,
                file_size=file_size,
                mime_type=active_version.mime_type,
                file_type=active_version.file_type,
                checksum=checksum,
                rows_count=len(cleaned_df),
                columns_count=len(cleaned_df.columns),
                status=DatasetStatus.CLEANED,
                is_current=True
            )
            await self.version_repo.create(new_version)
            
            # 3. Create cleaning job log
            rows_removed = sum(item["affected"] for item in summary if item["type"] in ["drop_duplicates", "remove_outliers"])
            duplicates_removed = sum(item["affected"] for item in summary if item["type"] == "drop_duplicates")
            missing_handled = sum(item["affected"] for item in summary if item["type"] == "fill_missing")
            outliers_handled = sum(item["affected"] for item in summary if item["type"] == "remove_outliers")
            
            job = CleaningJob(
                id=uuid4(),
                dataset_id=dataset_id,
                source_version_id=active_version.id,
                target_version_id=new_version.id,
                cleaning_summary=summary,
                rows_removed=rows_removed,
                duplicates_removed=duplicates_removed,
                missing_handled=missing_handled,
                outliers_handled=outliers_handled,
                cleaned_file_path=storage_path,
                execution_time_ms=execution_time_ms,
                engine_version="1.0"
            )
            await self.cleaning_repo.create(job)
            
            await self.session.flush()
            
            # 4. Auto-profile the cleaned version
            profiler = ProfilingService(self.session)
            await profiler.profile_dataset(dataset_id=dataset_id, user_id=user_id)
            
        except Exception as e:
            # Cleanup file on disk if DB save failed
            if os.path.exists(local_path):
                os.remove(local_path)
            raise BadRequestException(f"Failed to record cleaning job transaction: {str(e)}")
            
        # Expire the dataset in the session so it is reloaded from the database with fresh versions and profiles
        self.session.expire(dataset)
        return await self.dataset_repo.get_with_versions(dataset_id)

