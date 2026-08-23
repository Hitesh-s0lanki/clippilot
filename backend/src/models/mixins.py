"""Column helpers shared by every model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.types import UTCDateTime


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class UUIDPrimaryKey:
    """String UUID primary key.

    Stored as CHAR(36) rather than a native UUID type so the identical schema
    runs on both SQLite (local, tests) and Postgres (deployed).
    """

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid, sort_order=-100)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )
