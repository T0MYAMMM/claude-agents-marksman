"""Contracts for the plan / refinement / completion flow (protocol steps 2, 3, 5).

The agent sends raw Markdown content; the backend uploads it to the project's Drive
folder (centralising folder routing + the backoff/retry policy) and records a commit.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArtifactSubmit(BaseModel):
    """Markdown artifact an agent submits for upload to Drive."""

    agent_id: str
    file_name: str = Field(description="Drive file name, e.g. plan.md")
    content: str = Field(description="Full Markdown body (YAML frontmatter + content)")
    commit_message: str


class ArtifactResponse(BaseModel):
    """Result of recording a plan / revision / completion commit."""

    commit_id: str
    session_state: str
    gdrive_file_id: str
    web_view_link: str | None = None


class FeedbackCreate(BaseModel):
    """A reviewer comment submitted via the UI."""

    comment: str
    # Optional: defaults to the session's latest plan/revision commit.
    commit_id: str | None = None


class FeedbackRead(BaseModel):
    """Feedback as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    commit_id: str | None
    comment: str
    resolved: bool
    created_at: datetime


class StateResponse(BaseModel):
    """Generic session-state acknowledgement (e.g. after approval)."""

    session_id: str
    session_state: str
