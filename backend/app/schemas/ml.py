"""
Pydantic validation schemas for Machine Learning operations.
"""
from datetime import datetime
from typing import Any, List, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MLModelTrainRequest(BaseModel):
    """Schema representing a request to train a machine learning model."""
    target_column: str
    features: Optional[List[str]] = None
    problem_type: Optional[str] = "auto"
    candidate_algorithms: Optional[List[str]] = None
    cross_validation: bool = False
    random_state: int = 42


class MLModelResponse(BaseModel):
    """Schema representing the details of an MLModel record."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    dataset_version_id: UUID
    model_version: int
    target_column: str
    features: List[str]
    problem_type: str
    model_type: str
    status: str
    training_config: Dict[str, Any]
    evaluation_metrics: Optional[Dict[str, Any]] = None
    feature_importances: Optional[Dict[str, float]] = None
    model_size_bytes: Optional[int] = None
    dataset_quality_score: Optional[float] = None
    dataset_hash: Optional[str] = None
    best_score: Optional[float] = None
    training_log: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    training_rows: Optional[int] = None
    testing_rows: Optional[int] = None
    created_at: datetime


class PredictionRequest(BaseModel):
    """Schema representing an inference request payload."""
    input_data: Dict[str, Any]


class PredictionResponse(BaseModel):
    """Schema representing the prediction response payload."""
    prediction: Any
    confidence: Optional[float] = None


class PredictionLogResponse(BaseModel):
    """Schema representing an audited prediction history record."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_id: UUID
    input_payload: Dict[str, Any]
    prediction: str
    confidence: Optional[float] = None
    created_at: datetime
