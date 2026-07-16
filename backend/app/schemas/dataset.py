"""
Pydantic validation schemas for datasets and versions.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, computed_field
from app.common.enums import DatasetStatus
from app.schemas.data_profile import DataProfileResponse


class DatasetVersionResponse(BaseModel):
    """Schema representing metadata for a specific dataset version."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    version_number: int
    storage_path: str
    file_size: int
    mime_type: str
    file_type: str
    checksum: str
    rows_count: Optional[int]
    columns_count: Optional[int]
    status: DatasetStatus
    is_current: bool
    created_at: datetime


class DatasetResponse(BaseModel):
    """Lightweight representation of a dataset for collection responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    dataset_name: str
    original_filename: str
    description: Optional[str]
    source_type: Optional[str]
    created_at: datetime

    @computed_field
    def download_url(self) -> str:
        return f"/api/v1/datasets/{self.id}/download"

    @computed_field
    def preview_url(self) -> str:
        return f"/api/v1/datasets/{self.id}/preview"

    @computed_field
    def api_url(self) -> str:
        return f"/api/v1/datasets/{self.id}"


class DatasetDetailResponse(BaseModel):
    """Full detail of a dataset including its associated versions and profile."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    dataset_name: str
    original_filename: str
    description: Optional[str]
    source_type: Optional[str]
    created_at: datetime
    versions: List[DatasetVersionResponse]
    profile: Optional[DataProfileResponse] = None

    @computed_field
    def download_url(self) -> str:
        return f"/api/v1/datasets/{self.id}/download"

    @computed_field
    def preview_url(self) -> str:
        return f"/api/v1/datasets/{self.id}/preview"

    @computed_field
    def api_url(self) -> str:
        return f"/api/v1/datasets/{self.id}"
