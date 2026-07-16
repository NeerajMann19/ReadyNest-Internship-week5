"""
AiInsight database model.
"""
from uuid import UUID
from sqlalchemy import ForeignKey, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class AiInsight(UUIDMixin, TimestampMixin, Base):
    """
    AiInsight entity representing generated automated business and data quality insights.
    """
    __tablename__ = "ai_insights"

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    summary_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    insights_json: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    prompt_context_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    execution_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    engine_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0"
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="ai_insights")
