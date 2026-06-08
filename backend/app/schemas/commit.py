"""Response contracts for commit timeline reads."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CommitRead(BaseModel):
    """A single commit in the timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    agent_id: str
    type: str
    message: str
    parent_commit_id: str | None
    gdrive_ref_id: str | None
    payload: dict[str, Any] | None
    created_at: datetime


class CommitPage(BaseModel):
    """A keyset-paginated page of commits."""

    items: list[CommitRead]
    # Opaque cursor for the next page; null when no further pages remain.
    next_cursor: str | None = None
