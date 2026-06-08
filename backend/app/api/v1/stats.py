"""Dashboard metrics aggregation endpoint."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent
from app.models.commit import Commit
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project
from app.models.session import Session
from app.schemas.stats import (
    ActivityPoint,
    OverviewStats,
    RecentSession,
    StateCount,
    StatusCount,
    Totals,
    TypeCount,
)

router = APIRouter(prefix="/stats", tags=["stats"])

# Number of days (inclusive of today) covered by the activity sparkline.
_ACTIVITY_DAYS = 14


async def _count(db: AsyncSession, model: type) -> int:
    """Return the total row count for a model."""
    result = await db.execute(select(func.count()).select_from(model))
    return int(result.scalar_one())


@router.get("/overview", response_model=OverviewStats)
async def get_overview(db: AsyncSession = Depends(get_db)) -> OverviewStats:
    """Aggregate system-wide dashboard metrics in a single response."""
    # Totals.
    documents_result = await db.execute(
        select(func.count())
        .select_from(GDriveReference)
        .where(GDriveReference.category.is_not(None))
    )
    totals = Totals(
        projects=await _count(db, Project),
        sessions=await _count(db, Session),
        agents=await _count(db, Agent),
        commits=await _count(db, Commit),
        documents=int(documents_result.scalar_one()),
    )

    # Groupings (only existing rows; no synthesized zeros).
    state_rows = await db.execute(select(Session.state, func.count()).group_by(Session.state))
    sessions_by_state = [
        StateCount(state=str(state), count=int(count)) for state, count in state_rows.all()
    ]

    status_rows = await db.execute(select(Agent.status, func.count()).group_by(Agent.status))
    agents_by_status = [
        StatusCount(status=str(status), count=int(count)) for status, count in status_rows.all()
    ]

    type_rows = await db.execute(select(Commit.type, func.count()).group_by(Commit.type))
    commits_by_type = [
        TypeCount(type=str(ctype), count=int(count)) for ctype, count in type_rows.all()
    ]

    # Activity: commits per day over the last 14 days inclusive, zero-filled.
    # Bucket in Python for SQLite/Postgres portability (no DB date functions).
    now = datetime.now(UTC)
    today = now.date()
    window_start = today - timedelta(days=_ACTIVITY_DAYS - 1)
    since = datetime.combine(window_start, datetime.min.time(), tzinfo=UTC)

    created_rows = await db.execute(select(Commit.created_at).where(Commit.created_at >= since))
    buckets: dict[str, int] = {}
    for (created_at,) in created_rows.all():
        day = created_at.date().isoformat()
        buckets[day] = buckets.get(day, 0) + 1

    activity = [
        ActivityPoint(
            date=(d := (window_start + timedelta(days=offset)).isoformat()),
            commits=buckets.get(d, 0),
        )
        for offset in range(_ACTIVITY_DAYS)
    ]

    # Recent sessions: 5 most recent by started_at desc.
    recent_rows = await db.execute(select(Session).order_by(Session.started_at.desc()).limit(5))
    recent_sessions = [RecentSession.model_validate(s) for s in recent_rows.scalars()]

    return OverviewStats(
        totals=totals,
        sessions_by_state=sessions_by_state,
        agents_by_status=agents_by_status,
        commits_by_type=commits_by_type,
        activity=activity,
        recent_sessions=recent_sessions,
    )
