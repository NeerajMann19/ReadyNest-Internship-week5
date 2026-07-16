"""
Pydantic validation schemas for data cleaning operations.
"""
from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CleaningOperation(BaseModel):
    """Schema representing a single requested cleaning operation."""
    type: str
    column: Optional[str] = None
    strategy: Optional[str] = None
    target_type: Optional[str] = None
    fill_value: Optional[Any] = None


class CleanRequest(BaseModel):
    """Request payload containing ordered sequence of cleaning operations."""
    operations: List[CleaningOperation]


class CleanPreviewResponse(BaseModel):
    """Schema representing structural changes preview results."""
    before: Dict[str, Any]
    after: Dict[str, Any]
    changes: List[Dict[str, Any]]
    warnings: List[str]
    original_sample: List[Dict[str, Any]]
    cleaned_sample: List[Dict[str, Any]]


class CleaningJobResponse(BaseModel):
    """Schema representing completed cleaning job lineage log."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    source_version_id: UUID
    target_version_id: UUID
    cleaning_summary: List[Dict[str, Any]]
    rows_removed: int
    duplicates_removed: int
    missing_handled: int
    outliers_handled: int
    cleaned_file_path: str
    execution_time_ms: int
    engine_version: str
    created_at: datetime
