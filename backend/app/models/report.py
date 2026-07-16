"""
Report database model.
"""
from datetime import datetime
from uuid import UUID
from sqlalchemy import ForeignKey, String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class Report(UUIDMixin, TimestampMixin, Base):
    """
    Report entity representing a generated user report file (PDF, EXCEL, HTML, JSON).
    """
    __tablename__ = "reports"

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False
    )
    dataset_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING"
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=True
    )
    checksum_algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SHA-256"
    )
    generated_from_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    generation_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    report_schema_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0"
    )
    download_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    preview_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="reports")
