"""Reusable column mixins for primary keys and timestamps."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def _uuid_str() -> str:
    """Generate a hex UUID4 string. Portable across SQLite and Postgres."""
    return uuid4().hex


def _utcnow() -> datetime:
    """Timezone-aware current UTC time (avoids deprecated utcnow())."""
    return datetime.now(UTC)


class UUIDPrimaryKey:
    """Adds a string UUID primary key generated application-side."""

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)


class TimestampMixin:
    """Adds a created_at column populated on insert."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
