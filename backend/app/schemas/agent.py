"""Contracts for agent registration and listing (admin/operator surface)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    """Payload to register a new agent."""

    name: str = Field(min_length=1, max_length=255)
    tailscale_node: str | None = None


class AgentRead(BaseModel):
    """An agent as listed by the API. Never includes key material."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    tailscale_node: str | None
    status: str
    last_seen_at: datetime | None
    created_at: datetime


class AgentCreated(AgentRead):
    """Registration response. Carries the plaintext API key exactly once.

    The key is shown only here and never persisted in plaintext; store it now.
    """

    api_key: str
