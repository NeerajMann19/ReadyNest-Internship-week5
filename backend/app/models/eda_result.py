"""
EdaResult database model.
"""
from uuid import UUID
from sqlalchemy import ForeignKey, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class EdaResult(UUIDMixin, TimestampMixin, Base):
    """
    EdaResult entity representing stored exploratory data analysis metrics.
    """
    __tablename__ = "eda_results"

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
    statistics_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    charts_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )
    html_reports_json: Mapped[dict] = mapped_column(
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
    pandas_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="eda_results")
