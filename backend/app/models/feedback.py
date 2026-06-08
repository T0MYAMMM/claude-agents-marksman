"""Feedback model: a human comment on a plan, awaiting agent refinement."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey


class Feedback(Base, UUIDPrimaryKey, TimestampMixin):
    """A reviewer comment injected via the UI during the WAITING_FOR_HUMAN gate.

    Marked resolved once the agent incorporates it into a REVISION commit.
    """

    __tablename__ = "feedback"

    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The commit (plan/revision) this comment is attached to.
    commit_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("commits.id"), nullable=True
    )
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
