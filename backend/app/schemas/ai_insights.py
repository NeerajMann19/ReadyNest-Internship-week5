"""
Pydantic validation schemas for AI Insights results.
"""
from datetime import datetime
from typing import Dict, List, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AiInsightResponse(BaseModel):
    """Schema representing computed dataset AI Insights results."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    summary_json: Dict[str, Any]
    insights_json: List[Dict[str, Any]]
    prompt_context_json: Dict[str, Any]
    execution_time_ms: int
    engine_version: str
    created_at: datetime


class AiInsightSummaryResponse(BaseModel):
    """Schema representing lightweight executive health summary results."""
    overall_health: str
    quality_score: float
    total_insights_count: int
    priority_distribution: Dict[str, int]
