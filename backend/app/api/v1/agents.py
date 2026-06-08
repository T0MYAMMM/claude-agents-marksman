"""Agent check-in endpoint (protocol step 1: INIT)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import authenticate_agent, require_tailscale
from app.core.security import generate_api_key, hash_api_key
from app.database import get_db
from app.models.agent import Agent
from app.models.commit import Commit
from app.models.enums import AgentStatus, CommitType, SessionState
from app.models.feedback import Feedback
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project
from app.models.session import Session
from app.schemas.agent import AgentCreate, AgentCreated, AgentRead
from app.schemas.checkin import (
    CheckInContext,
    CheckInRequest,
    CheckInResponse,
    FeedbackItem,
    ProjectSummary,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "",
    response_model=AgentCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tailscale)],
)
async def register_agent(
    body: AgentCreate, db: AsyncSession = Depends(get_db)
) -> AgentCreated:
    """Register an agent and return its API key once (admin/operator action).

    The plaintext key is generated here, hashed for storage, and returned exactly once.
    It is never logged or persisted in plaintext.
    """
    api_key = generate_api_key()
    agent = Agent(
        name=body.name,
        tailscale_node=body.tailscale_node,
        api_key_hash=hash_api_key(api_key),
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentCreated(
        id=agent.id,
        name=agent.name,
        tailscale_node=agent.tailscale_node,
        status=agent.status.value,
        last_seen_at=agent.last_seen_at,
        created_at=agent.created_at,
        api_key=api_key,
    )


@router.get("", response_model=list[AgentRead], dependencies=[Depends(require_tailscale)])
async def list_agents(db: AsyncSession = Depends(get_db)) -> list[Agent]:
    """List registered agents (no key material)."""
    result = await db.execute(select(Agent).order_by(desc(Agent.created_at)))
    return list(result.scalars())


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_tailscale)],
)
async def revoke_agent(agent_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Revoke an agent's key (soft delete).

    Sets the agent to REVOKED so it can no longer authenticate, while preserving its
    sessions and audit trail. Idempotent for an already-revoked agent.
    """
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
    agent.status = AgentStatus.REVOKED
    await db.commit()


@router.post("/checkin", response_model=CheckInResponse)
async def check_in(
    body: CheckInRequest,
    agent: Agent = Depends(authenticate_agent),
    db: AsyncSession = Depends(get_db),
) -> CheckInResponse:
    """Authenticate an agent, attach it to a project, and return current context.

    Creates a fresh session in INIT state and surfaces the latest plan + any pending
    human feedback so the agent can resume coherently.
    """
    if agent.id != body.agent_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "API key does not match agent_id")

    project = await db.get(Project, body.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    now = datetime.now(UTC)
    agent.status = AgentStatus.ONLINE
    agent.last_seen_at = now
    if body.tailscale_node:
        agent.tailscale_node = body.tailscale_node

    session = Session(
        project_id=project.id,
        agent_id=agent.id,
        title=f"Session for {project.name}",
        state=SessionState.INIT,
    )
    db.add(session)
    await db.flush()

    context = await _build_context(db, project.id)

    await db.commit()
    return CheckInResponse(
        session_id=session.id,
        project=ProjectSummary(
            id=project.id, name=project.name, gdrive_folder_id=project.gdrive_folder_id
        ),
        state=session.state.value,
        context=context,
        server_time=now,
    )


async def _build_context(db: AsyncSession, project_id: str) -> CheckInContext:
    """Gather the latest plan commit for the project to hand back to the agent."""
    result = await db.execute(
        select(Commit)
        .join(Session, Commit.session_id == Session.id)
        .where(Session.project_id == project_id)
        .where(Commit.type.in_([CommitType.PLAN, CommitType.REVISION]))
        .order_by(desc(Commit.created_at))
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    if latest is None:
        return CheckInContext()

    plan_file_id: str | None = None
    if latest.gdrive_ref_id:
        ref = await db.get(GDriveReference, latest.gdrive_ref_id)
        plan_file_id = ref.gdrive_file_id if ref else None

    # Surface any unresolved reviewer feedback across the project's sessions.
    fb_rows = await db.execute(
        select(Feedback)
        .join(Session, Feedback.session_id == Session.id)
        .where(Session.project_id == project_id)
        .where(Feedback.resolved.is_(False))
        .order_by(desc(Feedback.created_at))
    )
    pending = [
        FeedbackItem(commit_id=f.commit_id or latest.id, comment=f.comment)
        for f in fb_rows.scalars()
    ]

    return CheckInContext(
        latest_commit_id=latest.id, latest_plan_file_id=plan_file_id, pending_feedback=pending
    )
