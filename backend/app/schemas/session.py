"""Read contracts for sessions (dashboard + session manager)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionRead(BaseModel):
    """A session as surfaced to the dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    agent_id: str
    title: str
    state: str
    user_prompt: str | None
    progress_pct: int
    started_at: datetime
    ended_at: datetime | None
