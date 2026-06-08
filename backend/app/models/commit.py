"""Commit model: an immutable, append-only version-control log entry."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CommitType
from app.models.mixins import UUIDPrimaryKey, _utcnow


class Commit(Base, UUIDPrimaryKey):
    """A single recorded agent action: plan, revision, stage report, or completion."""

    __tablename__ = "commits"
    __table_args__ = (
        # Keyset-pagination index for the timeline view (newest first per session).
        Index("idx_commits_session_time", "session_id", "created_at"),
    )

    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False
    )
    # Nullable: progress-only stage reports may carry no uploaded file.
    gdrive_ref_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("gdrive_references.id"), nullable=True
    )
    # Self-referential parent forms the Git-style commit tree (null = root).
    parent_commit_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("commits.id"), nullable=True, index=True
    )
    type: Mapped[CommitType] = mapped_column(
        Enum(CommitType, native_enum=False, length=16), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Stage-report body: completed tasks, blockers, minor changes.
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="commits")  # noqa: F821
    gdrive_ref: Mapped["GDriveReference | None"] = relationship()  # noqa: F821
