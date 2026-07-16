"""
Pydantic validation schemas for Reports and Bulk operations.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ReportRequest(BaseModel):
    """Schema representing request payload to compile reports."""
    report_type: str


class ReportResponse(BaseModel):
    """Schema representing generated report properties details."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    report_type: str
    status: str
    file_size: int
    checksum: Optional[str] = None
    checksum_algorithm: str
    generated_from_version: int
    generation_time_ms: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    report_schema_version: str
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    created_at: datetime


class DatasetCompareResponse(BaseModel):
    """Schema representing side-by-side versions comparison metadata."""
    version_difference: Dict[str, Any]
    columns_added: List[str]
    columns_removed: List[str]
    datatype_changes: Dict[str, Any]
    cleaning_operations_applied: List[Dict[str, Any]]
    profiling_difference: Dict[str, Any]
    insights_difference: Dict[str, Any]
    v1_metrics: Dict[str, Any]
    v2_metrics: Dict[str, Any]


class BulkDeleteRequest(BaseModel):
    """Schema representing request parameters list to bulk delete workspaces."""
    ids: List[UUID]


class BulkDeleteResponse(BaseModel):
    """Schema representing bulk operations execution details counts."""
    deleted: int
    failed: int
    total: int
