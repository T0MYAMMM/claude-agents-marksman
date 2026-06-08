"""Stage-report webhook listener (protocol step 4: EXECUTION & REPORTING)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import authenticate_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.enums import CommitType, SessionState
from app.models.gdrive_reference import GDriveReference
from app.models.session import Session
from app.schemas.stage_report import NextAction, StageReportRequest, StageReportResponse
from app.services.session_state import InvalidTransitionError, assert_transition
from app.services.version_control import record_commit

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/stage-report", response_model=StageReportResponse, status_code=status.HTTP_201_CREATED
)
async def stage_report(
    body: StageReportRequest,
    agent: Agent = Depends(authenticate_agent),
    db: AsyncSession = Depends(get_db),
) -> StageReportResponse:
    """Record a stage report as an immutable commit and advance session progress.

    If the report carries an artifact, a GDriveReference is created and linked. The
    session is kept in EXECUTING; the server returns a next_action so it can steer a
    polling agent (e.g. PAUSE_FOR_FEEDBACK once mid-execution feedback is enabled).
    """
    if agent.id != body.agent_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "API key does not match agent_id")

    session = await db.get(Session, body.session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if session.agent_id != agent.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Session belongs to a different agent")

    # First stage report transitions WAITING_FOR_HUMAN/INIT -> EXECUTING; subsequent
    # reports are EXECUTING -> EXECUTING (a legal self-transition).
    try:
        assert_transition(session.state, SessionState.EXECUTING)
    except InvalidTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    gdrive_ref: GDriveReference | None = None
    if body.artifact is not None:
        gdrive_ref = GDriveReference(
            gdrive_file_id=body.artifact.gdrive_file_id,
            file_name=body.artifact.file_name,
            web_view_link=body.artifact.web_view_link,
            drive_revision_id=body.artifact.drive_revision_id,
        )

    payload = {
        "stage": body.stage.model_dump(),
        "status": body.status.value,
        "completed_tasks": body.completed_tasks,
        "blockers": [b.model_dump() for b in body.blockers],
        "minor_changes": body.minor_changes,
    }

    commit = await record_commit(
        db,
        session_id=session.id,
        agent_id=agent.id,
        commit_type=CommitType.STAGE_REPORT,
        message=body.commit_message,
        gdrive_ref=gdrive_ref,
        payload=payload,
    )

    session.state = SessionState.EXECUTING
    session.progress_pct = body.progress_pct
    now = datetime.now(UTC)
    agent.last_seen_at = now

    await db.commit()
    return StageReportResponse(
        commit_id=commit.id,
        session_state=session.state.value,
        progress_pct=session.progress_pct,
        accepted_at=now,
        next_action=NextAction.CONTINUE,
    )
