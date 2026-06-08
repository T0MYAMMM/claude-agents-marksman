"""Session model: one agent run against one project and prompt."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SessionState
from app.models.mixins import UUIDPrimaryKey, _utcnow


class Session(Base, UUIDPrimaryKey):
    """A single agent workflow, tracked through the operational state machine."""

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("progress_pct >= 0 AND progress_pct <= 100", name="progress_valid"),
    )

    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[SessionState] = mapped_column(
        Enum(SessionState, native_enum=False, length=24),
        default=SessionState.INIT,
        nullable=False,
        index=True,
    )
    user_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_pct: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="sessions")  # noqa: F821
    agent: Mapped["Agent"] = relationship(back_populates="sessions")  # noqa: F821
    commits: Mapped[list["Commit"]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan"
    )
