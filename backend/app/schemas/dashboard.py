"""
Pydantic validation schemas for Dashboard summary aggregations.
"""
from typing import Dict, List, Any
from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    """Schema representing consolidated dashboard analytics summary data."""
    kpis: Dict[str, Any]
    charts: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    recent_datasets: List[Dict[str, Any]]
    recent_cleaning_jobs: List[Dict[str, Any]]
    recent_insights: List[Dict[str, Any]]
    recent_reports: List[Dict[str, Any]]
    metadata: Dict[str, Any]

