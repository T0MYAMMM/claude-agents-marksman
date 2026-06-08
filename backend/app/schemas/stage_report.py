"""Request/response contracts for stage reports (protocol step 4: EXECUTION & REPORTING)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class StageStatus(StrEnum):
    """Status of the reported stage."""

    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class NextAction(StrEnum):
    """Instruction the server returns to steer the polling agent."""

    CONTINUE = "CONTINUE"
    PAUSE_FOR_FEEDBACK = "PAUSE_FOR_FEEDBACK"
    ABORT = "ABORT"


class StageInfo(BaseModel):
    """Which stage of the plan this report concerns."""

    index: int = Field(ge=0)
    name: str
    of_total: int = Field(ge=1)


class Blocker(BaseModel):
    """A blocker the agent encountered."""

    severity: str
    detail: str


class ArtifactRef(BaseModel):
    """Pointer to the Markdown report uploaded to Drive for this stage (optional)."""

    gdrive_file_id: str
    file_name: str
    drive_revision_id: str | None = None
    web_view_link: str | None = None


class StageReportRequest(BaseModel):
    """Body an agent POSTs to /webhooks/stage-report."""

    session_id: str
    agent_id: str
    stage: StageInfo
    progress_pct: int = Field(ge=0, le=100)
    status: StageStatus = StageStatus.IN_PROGRESS
    completed_tasks: list[str] = Field(default_factory=list)
    blockers: list[Blocker] = Field(default_factory=list)
    minor_changes: list[str] = Field(default_factory=list)
    artifact: ArtifactRef | None = None
    commit_message: str


class StageReportResponse(BaseModel):
    """Acknowledgement returned after a stage report is recorded as a commit."""

    commit_id: str
    session_state: str
    progress_pct: int
    accepted_at: datetime
    next_action: NextAction
