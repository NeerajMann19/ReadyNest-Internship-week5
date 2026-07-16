"""
Pydantic validation schemas for data profiling results.
"""
from datetime import datetime
from typing import Any, List, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DataProfileResponse(BaseModel):
    """Schema representing generated dataset profiling results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    missing_values: int
    duplicate_rows: int
    memory_usage_bytes: int
    column_summary: List[Dict[str, Any]]
    quality_score: float
    created_at: datetime
