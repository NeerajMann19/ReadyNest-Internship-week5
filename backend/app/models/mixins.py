"""
Common SQLAlchemy model mixins.
"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class UUIDMixin:
    """
    Mixin adding a UUID primary key 'id' to models.
    """
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )


class TimestampMixin:
    """
    Mixin adding automatic created_at and updated_at datetime tracking.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
