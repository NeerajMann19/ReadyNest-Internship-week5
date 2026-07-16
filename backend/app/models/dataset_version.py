"""
DatasetVersion database model.
"""
from uuid import UUID
from sqlalchemy import ForeignKey, String, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin
from app.common.enums import DatasetStatus


class DatasetVersion(UUIDMixin, TimestampMixin, Base):
    """
    DatasetVersion entity representing a specific immutable iteration of a dataset workspace.
    """
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )
    rows_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    columns_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    status: Mapped[DatasetStatus] = mapped_column(
        SQLEnum(DatasetStatus),
        default=DatasetStatus.UPLOADED,
        nullable=False
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="versions")
