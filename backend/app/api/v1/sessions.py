"""Session protocol endpoints: plan, refine, feedback, approve, complete.

Agent-driven steps (plan/refine/complete) authenticate with the agent API key.
Human-driven steps (feedback/approve) come from the dashboard and use the Tailscale
network guard only (no per-user auth module is specified in the architecture).
"""

from datetime import UTC, datetime

from anyio import to_thread
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import authenticate_agent, require_tailscale
from app.database import get_db
from app.deps import get_gdrive
from app.models.agent import Agent
from app.models.commit import Commit
from app.models.enums import AgentStatus, CommitType, SessionState
from app.models.feedback import Feedback
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project
from app.models.session import Session
from app.schemas.bookshelf import DocumentSubmit
from app.schemas.plan import (
    ArtifactResponse,
    ArtifactSubmit,
    FeedbackCreate,
    FeedbackRead,
    StateResponse,
)
from app.schemas.session import SessionRead
from app.services.artifact import ensure_project_bookshelf, upload_and_commit
from app.services.gdrive import GDriveClient
from app.services.session_state import InvalidTransitionError, assert_transition

router = APIRouter(prefix="/sessions", tags=["sessions"])


# --------------------------------------------------------------------------- #
# Read endpoints (dashboard / session manager)
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[SessionRead])
async def list_sessions(
    db: AsyncSession = Depends(get_db), project_id: str | None = None
) -> list[Session]:
    """List sessions, optionally filtered to one project (newest first)."""
    stmt = select(Session)
    if project_id is not None:
        stmt = stmt.where(Session.project_id == project_id)
    stmt = stmt.order_by(desc(Session.started_at))
    return list((await db.execute(stmt)).scalars())


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)) -> Session:
    """Fetch a single session."""
    return await _load_session(db, session_id)


async def _load_session(db: AsyncSession, session_id: str) -> Session:
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return session


async def _project_folder(db: AsyncSession, session: Session) -> str:
    """Return the Drive folder for a session's project (explicit load; no async lazy-load)."""
    project = await db.get(Project, session.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project.gdrive_folder_id


def _transition(session: Session, target: SessionState) -> None:
    try:
        assert_transition(session.state, target)
    except InvalidTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    session.state = target


# --------------------------------------------------------------------------- #
# Agent-driven steps
# --------------------------------------------------------------------------- #
@router.post("/{session_id}/plan", response_model=ArtifactResponse, status_code=201)
async def submit_plan(
    session_id: str,
    body: ArtifactSubmit,
    agent: Agent = Depends(authenticate_agent),
    db: AsyncSession = Depends(get_db),
    gdrive: GDriveClient = Depends(get_gdrive),
) -> ArtifactResponse:
    """Protocol step 2 (PLANNING): upload the initial plan, then await human review."""
    session = await _load_session(db, session_id)
    if session.agent_id != agent.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Session belongs to a different agent")

    _transition(session, SessionState.PLANNING)
    folder = await _project_folder(db, session)
    commit, ref = await upload_and_commit(
        db,
        gdrive,
        session_id=session.id,
        agent_id=agent.id,
        gdrive_folder_id=folder,
        file_name=body.file_name,
        content=body.content,
        commit_type=CommitType.PLAN,
        message=body.commit_message,
    )
    _transition(session, SessionState.WAITING_FOR_HUMAN)
    await db.commit()
    return ArtifactResponse(
        commit_id=commit.id,
        session_state=session.state.value,
        gdrive_file_id=ref.gdrive_file_id,
        web_view_link=ref.web_view_link,
    )


@router.post("/{session_id}/refine", response_model=ArtifactResponse, status_code=201)
async def refine_plan(
    session_id: str,
    body: ArtifactSubmit,
    agent: Agent = Depends(authenticate_agent),
    db: AsyncSession = Depends(get_db),
    gdrive: GDriveClient = Depends(get_gdrive),
) -> ArtifactResponse:
    """Protocol step 3 (REFINEMENT): upload a revised plan and resolve open feedback."""
    session = await _load_session(db, session_id)
    if session.agent_id != agent.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Session belongs to a different agent")

    folder = await _project_folder(db, session)
    commit, ref = await upload_and_commit(
        db,
        gdrive,
        session_id=session.id,
        agent_id=agent.id,
        gdrive_folder_id=folder,
        file_name=body.file_name,
        content=body.content,
        commit_type=CommitType.REVISION,
        message=body.commit_message,
    )
    # Mark all open feedback for this session resolved.
    await db.execute(
        update(Feedback)
        .where(Feedback.session_id == session.id, Feedback.resolved.is_(False))
        .values(resolved=True)
    )
    _transition(session, SessionState.WAITING_FOR_HUMAN)
    await db.commit()
    return ArtifactResponse(
        commit_id=commit.id,
        session_state=session.state.value,
        gdrive_file_id=ref.gdrive_file_id,
        web_view_link=ref.web_view_link,
    )


@router.post("/{session_id}/complete", response_model=ArtifactResponse, status_code=201)
async def complete_session(
    session_id: str,
    body: ArtifactSubmit,
    agent: Agent = Depends(authenticate_agent),
    db: AsyncSession = Depends(get_db),
    gdrive: GDriveClient = Depends(get_gdrive),
) -> ArtifactResponse:
    """Protocol step 5 (COMPLETION): upload the final artifact and close the session."""
    session = await _load_session(db, session_id)
    if session.agent_id != agent.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Session belongs to a different agent")

    folder = await _project_folder(db, session)
    commit, ref = await upload_and_commit(
        db,
        gdrive,
        session_id=session.id,
        agent_id=agent.id,
        gdrive_folder_id=folder,
        file_name=body.file_name,
        content=body.content,
        commit_type=CommitType.COMPLETION,
        message=body.commit_message,
    )
    _transition(session, SessionState.COMPLETED)
    session.progress_pct = 100
    session.ended_at = datetime.now(UTC)
    agent.status = AgentStatus.OFFLINE
    await db.commit()
    return ArtifactResponse(
        commit_id=commit.id,
        session_state=session.state.value,
        gdrive_file_id=ref.gdrive_file_id,
        web_view_link=ref.web_view_link,
    )


@router.post("/{session_id}/document", response_model=ArtifactResponse, status_code=201)
async def submit_document(
    session_id: str,
    body: DocumentSubmit,
    agent: Agent = Depends(authenticate_agent),
    db: AsyncSession = Depends(get_db),
    gdrive: GDriveClient = Depends(get_gdrive),
) -> ArtifactResponse:
    """Upload a documentation artifact to the project's bookshelf (no state change)."""
    session = await _load_session(db, session_id)
    if session.agent_id != agent.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Session belongs to a different agent")

    project = await db.get(Project, session.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    # Idempotent upsert: if a doc with the same name already exists in this category for
    # the project, overwrite it in place instead of appending a duplicate to the shelf.
    existing = (
        await db.execute(
            select(GDriveReference)
            .join(Commit, Commit.gdrive_ref_id == GDriveReference.id)
            .join(Session, Session.id == Commit.session_id)
            .where(Session.project_id == project.id)
            .where(GDriveReference.category == body.category)
            .where(GDriveReference.file_name == body.file_name)
            .order_by(desc(GDriveReference.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    if existing is not None:
        meta = await to_thread.run_sync(
            gdrive.update_markdown, existing.gdrive_file_id, body.content
        )
        existing.drive_revision_id = meta.get("drive_revision_id") or existing.drive_revision_id
        commit = (
            await db.execute(
                select(Commit)
                .where(Commit.gdrive_ref_id == existing.id)
                .order_by(desc(Commit.created_at))
                .limit(1)
            )
        ).scalar_one_or_none()
        if commit is not None:
            commit.message = body.commit_message
        await db.commit()
        return ArtifactResponse(
            commit_id=commit.id if commit else existing.id,
            session_state=session.state.value,
            gdrive_file_id=existing.gdrive_file_id,
            web_view_link=existing.web_view_link,
        )

    sections = await ensure_project_bookshelf(db, gdrive, project)
    folder_id = sections[body.category.value]
    commit, ref = await upload_and_commit(
        db,
        gdrive,
        session_id=session.id,
        agent_id=agent.id,
        gdrive_folder_id=folder_id,
        file_name=body.file_name,
        content=body.content,
        commit_type=CommitType.DOC,
        message=body.commit_message,
        category=body.category,
    )
    await db.commit()
    return ArtifactResponse(
        commit_id=commit.id,
        session_state=session.state.value,
        gdrive_file_id=ref.gdrive_file_id,
        web_view_link=ref.web_view_link,
    )


# --------------------------------------------------------------------------- #
# Human-driven steps (dashboard UI)
# --------------------------------------------------------------------------- #
@router.post(
    "/{session_id}/feedback",
    response_model=FeedbackRead,
    status_code=201,
    dependencies=[Depends(require_tailscale)],
)
async def submit_feedback(
    session_id: str, body: FeedbackCreate, db: AsyncSession = Depends(get_db)
) -> Feedback:
    """A reviewer injects feedback during the WAITING_FOR_HUMAN gate -> REFINING."""
    session = await _load_session(db, session_id)
    _transition(session, SessionState.REFINING)

    commit_id = body.commit_id
    if commit_id is None:
        result = await db.execute(
            select(Commit.id)
            .where(Commit.session_id == session.id)
            .where(Commit.type.in_([CommitType.PLAN, CommitType.REVISION]))
            .order_by(desc(Commit.created_at))
            .limit(1)
        )
        commit_id = result.scalar_one_or_none()

    feedback = Feedback(session_id=session.id, commit_id=commit_id, comment=body.comment)
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@router.post(
    "/{session_id}/approve",
    response_model=StateResponse,
    dependencies=[Depends(require_tailscale)],
)
async def approve_plan(session_id: str, db: AsyncSession = Depends(get_db)) -> StateResponse:
    """A reviewer approves the plan -> EXECUTING."""
    session = await _load_session(db, session_id)
    _transition(session, SessionState.EXECUTING)
    await db.commit()
    return StateResponse(session_id=session.id, session_state=session.state.value)


@router.get("/{session_id}/feedback", response_model=list[FeedbackRead])
async def list_feedback(
    session_id: str, db: AsyncSession = Depends(get_db), unresolved_only: bool = False
) -> list[Feedback]:
    """List feedback for a session (Session/Topic Manager UI)."""
    stmt = select(Feedback).where(Feedback.session_id == session_id)
    if unresolved_only:
        stmt = stmt.where(Feedback.resolved.is_(False))
    stmt = stmt.order_by(desc(Feedback.created_at))
    return list((await db.execute(stmt)).scalars())
