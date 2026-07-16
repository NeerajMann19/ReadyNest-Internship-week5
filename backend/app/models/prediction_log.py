"""
PredictionLog database model.
"""
from uuid import UUID
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import ForeignKey, String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.mixins import UUIDMixin


class PredictionLog(UUIDMixin, Base):
    """
    PredictionLog entity representing an audited inference calculation using a trained ML model.
    """
    __tablename__ = "prediction_logs"

    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False
    )
    input_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    prediction: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    model: Mapped["MLModel"] = relationship(back_populates="prediction_logs")
