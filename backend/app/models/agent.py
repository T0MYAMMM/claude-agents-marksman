"""Agent model: a registered AI worker."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AgentStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKey


class Agent(Base, UUIDPrimaryKey, TimestampMixin):
    """An AI agent authorised to check in over the Tailscale network."""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Argon2 hash of the agent's API key — the plaintext key is never stored.
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    tailscale_node: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, native_enum=False, length=16),
        default=AgentStatus.OFFLINE,
        nullable=False,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["Session"]] = relationship(back_populates="agent")  # noqa: F821
