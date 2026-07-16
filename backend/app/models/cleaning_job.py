"""
CleaningJob database model.
"""
from uuid import UUID
from sqlalchemy import ForeignKey, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class CleaningJob(UUIDMixin, TimestampMixin, Base):
    """
    CleaningJob entity representing history of data cleaning transitions.
    """
    __tablename__ = "cleaning_jobs"

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False
    )
    source_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False
    )
    target_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False
    )
    cleaning_summary: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
    rows_removed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    duplicates_removed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    missing_handled: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    outliers_handled: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    cleaned_file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
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
    dataset: Mapped["Dataset"] = relationship(back_populates="cleaning_jobs")
