"""
MLModel database model.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class MLModel(UUIDMixin, TimestampMixin, Base):
    """
    MLModel entity representing a trained machine learning model associated with a dataset version.
    """
    __tablename__ = "ml_models"

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False
    )
    model_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    target_column: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )
    features: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False
    )
    problem_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    model_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False
    )
    training_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    evaluation_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=True
    )
    feature_importances: Mapped[Dict[str, float]] = mapped_column(
        JSON,
        nullable=True
    )
    model_path: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    model_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    dataset_quality_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )
    dataset_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=True
    )
    best_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )
    training_log: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    error_message: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    training_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    testing_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="ml_models")
    prediction_logs: Mapped[List["PredictionLog"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan"
    )
