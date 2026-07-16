"""
DataProfile database model.
"""
from uuid import UUID
from sqlalchemy import ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class DataProfile(UUIDMixin, TimestampMixin, Base):
    """
    DataProfile entity representing computed metadata results for a dataset workspace.
    """
    __tablename__ = "data_profiles"

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    missing_values: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    duplicate_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    memory_usage_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    column_summary: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    quality_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="profile")
