"""
Pydantic validation schemas for Exploratory Data Analysis (EDA) results.
"""
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class EdaResultResponse(BaseModel):
    """Schema representing computed Exploratory Data Analysis (EDA) results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    summary_json: Dict[str, Any]
    statistics_json: Dict[str, Any]
    charts_json: Dict[str, Any]
    html_reports_json: Dict[str, Any]
    execution_time_ms: int
    engine_version: str
    pandas_version: str
    created_at: datetime
