"""
Dataset database model.
"""
from uuid import UUID
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from app.db.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class Dataset(UUIDMixin, TimestampMixin, Base):
    """
    Dataset root metadata tracking entity. Represents a user's uploaded dataset workspace.
    """
    __tablename__ = "datasets"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    dataset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship()
    versions: Mapped[List["DatasetVersion"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    profile: Mapped[Optional["DataProfile"]] = relationship(
        back_populates="dataset",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    cleaning_jobs: Mapped[List["CleaningJob"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    eda_results: Mapped[List["EdaResult"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    ai_insights: Mapped[List["AiInsight"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    ml_models: Mapped[List["MLModel"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

