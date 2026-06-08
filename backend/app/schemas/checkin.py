"""Request/response contracts for agent check-in (protocol step 1: INIT)."""

from datetime import datetime

from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    """Body an agent POSTs to /agents/checkin. The API key travels in the X-Agent-Key header."""

    agent_id: str
    project_id: str
    tailscale_node: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class FeedbackItem(BaseModel):
    """A pending human comment the agent should address."""

    commit_id: str
    comment: str


class CheckInContext(BaseModel):
    """Latest project context handed back to the agent on check-in."""

    latest_commit_id: str | None = None
    latest_plan_file_id: str | None = None
    pending_feedback: list[FeedbackItem] = Field(default_factory=list)


class ProjectSummary(BaseModel):
    """Minimal project info the agent needs to operate."""

    id: str
    name: str
    gdrive_folder_id: str


class CheckInResponse(BaseModel):
    """Response returned to an authenticated agent."""

    session_id: str
    project: ProjectSummary
    state: str
    context: CheckInContext
    server_time: datetime
