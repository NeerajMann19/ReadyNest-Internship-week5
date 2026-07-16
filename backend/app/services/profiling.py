"""
Dataset automated profiling service logic.
"""
import os
import math
from typing import Optional, List
from uuid import UUID, uuid4
import pandas as pd
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dataset_version import DatasetVersion


from app.core.config import settings
from app.common.enums import DatasetStatus
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.data_profile import DataProfile
from app.repositories.data_profile import DataProfileRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.storage.local import LocalStorageService
from app.importing.parsers.csv import CSVParser
from app.importing.parsers.excel import ExcelParser


class ProfilingService:
    """
    Computes comprehensive structural and quality metadata profile for datasets.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.profile_repo = DataProfileRepository(session)
        self.storage_service = LocalStorageService()

    async def profile_dataset(self, dataset_id: UUID, user_id: UUID) -> DataProfile:
        """
        Executes automated profiling runner: parses dataframe, computes columns summary,
        deduces quality score, and overwrites existing profile record.
        """
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")



        version = await self.version_repo.get_current_version(dataset_id)
        if not version:
            raise BadRequestException("Dataset contains no active version to profile")



        # Map local file path
        local_path = version.storage_path.replace("local://", "", 1)
        ext = os.path.splitext(version.storage_path)[1].lower()

        # Instantiate appropriate parser
        parser = CSVParser() if ext == ".csv" else ExcelParser()
        try:
            df = parser.parse(local_path)
        except Exception as e:
            raise BadRequestException(f"Failed to load dataset for profiling: {str(e)}")

        # Execute vectorized calculations
        rows_count = len(df)
        columns_count = len(df.columns)
        total_cells = rows_count * columns_count
        memory_usage_bytes = int(df.memory_usage(deep=True).sum())
        duplicate_rows = int(df.duplicated().sum())
        missing_values = int(df.isna().sum().sum())

        column_summary = []

        for column in df.columns:
            col_series = df[column]
            missing_count = int(col_series.isna().sum())
            missing_pct = float((missing_count / rows_count) * 100.0) if rows_count > 0 else 0.0
            unique_count = int(col_series.nunique())

            # Heuristics for data type inference
            dtype_str = "text"
            if pd.api.types.is_bool_dtype(col_series):
                dtype_str = "boolean"
            elif pd.api.types.is_numeric_dtype(col_series):
                dtype_str = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(col_series):
                dtype_str = "datetime"
            else:
                # Try parsing as datetime if object type
                try:
                    sample_non_nulls = col_series.dropna().head(10)
                    if not sample_non_nulls.empty:
                        pd.to_datetime(sample_non_nulls)
                        dtype_str = "datetime"
                except Exception:
                    pass

                if dtype_str != "datetime":
                    # Check categoricals vs text
                    if unique_count < 20 or (rows_count > 0 and (unique_count / rows_count) < 0.05):
                        dtype_str = "categorical"

            # Parse sample unique values safely
            raw_samples = col_series.dropna().unique()[:5]
            sample_values = []
            for val in raw_samples:
                if hasattr(val, "item"):  # Convert numpy scalars to python types
                    sample_values.append(val.item())
                elif isinstance(val, (int, float, str, bool)):
                    # Guard float NaN/Inf
                    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                        continue
                    sample_values.append(val)
                else:
                    sample_values.append(str(val))

            col_stats = {
                "name": str(column),
                "dtype": dtype_str,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "sample_values": sample_values
            }

            # Calculate dtype-specific metrics
            if dtype_str == "numeric":
                col_stats["mean"] = float(col_series.mean()) if not pd.isna(col_series.mean()) else None
                col_stats["median"] = float(col_series.median()) if not pd.isna(col_series.median()) else None
                col_stats["min"] = float(col_series.min()) if not pd.isna(col_series.min()) else None
                col_stats["max"] = float(col_series.max()) if not pd.isna(col_series.max()) else None
                col_stats["std"] = float(col_series.std()) if not pd.isna(col_series.std()) else None
            elif dtype_str in ["text", "categorical"]:
                lengths = col_series.astype(str).str.len()
                col_stats["avg_length"] = float(lengths.mean()) if not pd.isna(lengths.mean()) else 0.0
                col_stats["max_length"] = int(lengths.max()) if not pd.isna(lengths.max()) else 0
            elif dtype_str == "datetime":
                try:
                    dt_series = pd.to_datetime(col_series, errors='coerce')
                    min_dt = dt_series.min()
                    max_dt = dt_series.max()
                    col_stats["min_date"] = min_dt.isoformat() if not pd.isna(min_dt) else None
                    col_stats["max_date"] = max_dt.isoformat() if not pd.isna(max_dt) else None
                except Exception:
                    col_stats["min_date"] = None
                    col_stats["max_date"] = None

            column_summary.append(col_stats)

        # Quality Score Calculation
        quality_score = 100.0
        if total_cells > 0:
            missing_ratio = missing_values / total_cells
            quality_score -= missing_ratio * settings.QUALITY_MISSING_WEIGHT
        if rows_count > 0:
            duplicate_ratio = duplicate_rows / rows_count
            quality_score -= duplicate_ratio * settings.QUALITY_DUPLICATE_WEIGHT

        quality_score = max(0.0, min(100.0, float(quality_score)))

        # Clean old profiles to support pure overwrite/reprofile logic
        existing_profile = await self.profile_repo.get_by_dataset_id(dataset_id)
        if existing_profile:
            await self.profile_repo.delete(existing_profile.id)

        # Save fresh DataProfile
        profile = DataProfile(
            id=uuid4(),
            dataset_id=dataset_id,
            missing_values=missing_values,
            duplicate_rows=duplicate_rows,
            memory_usage_bytes=memory_usage_bytes,
            column_summary=column_summary,
            quality_score=quality_score
        )
        await self.profile_repo.create(profile)

        # Update dataset version status to PROFILED
        version.status = DatasetStatus.PROFILED
        await self.version_repo.update(version, {"status": DatasetStatus.PROFILED})
        
        await self.session.flush()

        return profile

    async def get_profile(self, dataset_id: UUID, user_id: UUID) -> DataProfile:
        """
        Retrieves existing profile metadata. Raises NotFoundException if profiling hasn't run yet.
        """
        dataset = await self.dataset_repo.get(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        profile = await self.profile_repo.get_by_dataset_id(dataset_id)
        if not profile:
            raise NotFoundException("No profile generated yet for this dataset")
        return profile
