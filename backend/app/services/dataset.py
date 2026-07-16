"""
Dataset management service logic.
"""
import os
import math
import pandas as pd
from typing import List, Optional, Tuple, Any
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.common.enums import DatasetStatus
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.storage.local import LocalStorageService
from app.importing.parsers.csv import CSVParser
from app.importing.parsers.excel import ExcelParser


class DatasetService:
    """
    Orchestration service for dataset imports, storage management, and database persistence.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.storage_service = LocalStorageService()

    def _sanitize_floats(self, obj: Any) -> Any:
        """Recursively replaces float NaN/Inf with None to guarantee clean JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._sanitize_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_floats(x) for x in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        return obj

    async def import_dataset(
        self,
        user_id: UUID,
        upload_file: UploadFile,
        dataset_name: str,
        description: Optional[str] = None
    ) -> Tuple[Dataset, DatasetVersion]:
        """
        Ingests an uploaded dataset file: streams to local disk, runs checksums,
        parses schema details, and persists metadata in database.
        """
        filename = upload_file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise BadRequestException(f"Unsupported file extension '{ext}'. Only CSV and Excel are supported.")
            
        dataset_id = uuid4()
        
        # Save file to structured directory stream
        try:
            storage_path, file_size, checksum = self.storage_service.save_upload(
                upload_file=upload_file,
                user_id=user_id,
                dataset_id=dataset_id,
                version=1,
                ext=ext
            )
        except Exception as e:
            raise BadRequestException(f"File upload stream failed: {str(e)}")
            
        # Parse rows/cols metadata count using appropriate parser
        local_path = storage_path.replace("local://", "", 1)
        parser = CSVParser() if ext == ".csv" else ExcelParser()
        try:
            df = parser.parse(local_path)
            parser.validate(df)
            meta = parser.extract_metadata(df)
        except Exception as e:
            self.storage_service.delete_file(storage_path)
            raise BadRequestException(f"Failed to parse uploaded dataset file: {str(e)}")

            
        # Persist Dataset and Version records
        try:
            dataset = Dataset(
                id=dataset_id,
                user_id=user_id,
                dataset_name=dataset_name,
                original_filename=filename,
                description=description,
                source_type="UPLOAD"
            )
            await self.dataset_repo.create(dataset)
            
            dataset_version = DatasetVersion(
                id=uuid4(),
                dataset_id=dataset_id,
                version_number=1,
                storage_path=storage_path,
                file_size=file_size,
                mime_type=upload_file.content_type or "application/octet-stream",
                file_type=ext.replace(".", ""),
                checksum=checksum,
                rows_count=meta["rows_count"],
                columns_count=meta["columns_count"],
                status=DatasetStatus.UPLOADED,
                is_current=True
            )
            await self.version_repo.create(dataset_version)
            await self.session.flush()
        except Exception as e:
            self.storage_service.delete_file(storage_path)
            raise BadRequestException(f"Failed to record dataset metadata: {str(e)}")
        
        return dataset, dataset_version

    async def list_datasets(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort: Optional[str] = None,
        created_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None
    ) -> List[Dataset]:
        """
        Retrieves user owned datasets metadata with filtering and pagination.
        """
        stmt = select(Dataset).filter_by(user_id=user_id)
        
        # 1. Search filter
        if search:
            stmt = stmt.filter(Dataset.dataset_name.ilike(f"%{search}%"))
            
        # 2. Created before/after
        if created_before:
            stmt = stmt.filter(Dataset.created_at <= created_before)
        if created_after:
            stmt = stmt.filter(Dataset.created_at >= created_after)
            
        # 3. Sort logic
        if sort:
            parts = sort.split(":")
            col = parts[0]
            direction = parts[1] if len(parts) > 1 else "asc"
            
            if col == "dataset_name":
                stmt = stmt.order_by(Dataset.dataset_name.desc() if direction == "desc" else Dataset.dataset_name.asc())
            elif col == "created_at":
                stmt = stmt.order_by(Dataset.created_at.desc() if direction == "desc" else Dataset.created_at.asc())
        else:
            stmt = stmt.order_by(Dataset.created_at.desc())
            
        # 4. Status filter
        if status:
            stmt = stmt.join(Dataset.versions).filter(
                DatasetVersion.is_current == True,
                DatasetVersion.status == status
            )
            
        # Offset and limit
        stmt = stmt.offset(skip).limit(limit).options(selectinload(Dataset.versions), selectinload(Dataset.profile))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


    async def get_dataset(self, dataset_id: UUID, user_id: UUID) -> Dataset:
        """
        Resolves a user-owned dataset by ID, eagerly fetching details.
        """
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")
        return dataset

    async def get_dataset_file_path(self, dataset_id: UUID, user_id: UUID) -> str:
        """
        Resolves the local filepath for the current active version of a dataset.
        """
        dataset = await self.get_dataset(dataset_id, user_id)
        version = next((v for v in dataset.versions if v.is_current), None)
        if not version:
            raise BadRequestException("Dataset contains no active version")
            
        local_path = version.storage_path.replace("local://", "", 1)
        if not os.path.exists(local_path):
            raise NotFoundException("Dataset file not found on disk")
        return local_path

    async def preview_dataset_records(
        self,
        dataset_id: UUID,
        user_id: UUID,
        page: int,
        page_size: int,
        sort: Optional[str] = None,
        filter: Optional[str] = None
    ) -> dict:
        """
        Loads the active dataset version, applies sorting/filtering/pagination in-memory,
        and returns paginated preview + head(100) and tail(100).
        """
        dataset = await self.get_dataset(dataset_id, user_id)
        version = next((v for v in dataset.versions if v.is_current), None)
        if not version:
            raise BadRequestException("Dataset contains no active version")
            
        local_path = version.storage_path.replace("local://", "", 1)
        ext = os.path.splitext(version.storage_path)[1].lower()
        
        parser = CSVParser() if ext == ".csv" else ExcelParser()
        try:
            df = parser.parse(local_path)
        except Exception as e:
            raise BadRequestException(f"Failed to load dataset file: {str(e)}")
            
        # Apply filter
        if filter:
            # Search over string values of all columns
            mask = df.astype(str).apply(lambda row: row.str.contains(filter, case=False).any(), axis=1)
            df = df[mask]
            
        # Apply sort
        if sort:
            parts = sort.split(":")
            col = parts[0]
            ascending = True
            if len(parts) > 1 and parts[1].lower() == "desc":
                ascending = False
            if col in df.columns:
                df = df.sort_values(by=col, ascending=ascending)
                
        total_rows = len(df)
        total_columns = len(df.columns)
        
        start = (page - 1) * page_size
        end = start + page_size
        paginated_df = df.iloc[start:end]
        
        # Head (100) and Tail (100)
        head_df = df.head(100)
        tail_df = df.tail(100)
        
        preview_data = {
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "data": self._sanitize_floats(paginated_df.to_dict(orient="records")),
            "head_100": self._sanitize_floats(head_df.to_dict(orient="records")),
            "tail_100": self._sanitize_floats(tail_df.to_dict(orient="records"))
        }
        
        return preview_data

    async def bulk_delete_datasets(self, ids: List[UUID], user_id: UUID) -> dict:
        """
        Deletes multiple user datasets, physical files, and related tables cascade logs.
        """
        deleted = 0
        failed = 0
        total = len(ids)
        
        for d_id in ids:
            try:
                dataset = await self.dataset_repo.get_with_versions(d_id)
                if not dataset or dataset.user_id != user_id:
                    failed += 1
                    continue
                    
                # Purge files
                for version in dataset.versions:
                    local_path = version.storage_path.replace("local://", "", 1)
                    self.storage_service.delete_file(local_path)
                    
                await self.dataset_repo.delete(d_id)
                deleted += 1
            except Exception:
                failed += 1
                
        await self.session.commit()
        return {
            "deleted": deleted,
            "failed": failed,
            "total": total
        }

