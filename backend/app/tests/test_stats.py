"""Tests for the dashboard metrics overview endpoint."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.commit import Commit
from app.models.enums import AgentStatus, CommitType, DocCategory, SessionState
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project
from app.models.session import Session


@pytest.mark.asyncio
async def test_overview_aggregates_metrics(
    client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
    agent_and_key: tuple[Agent, str],
) -> None:
    """GET /stats/overview returns correct totals, groupings, activity, and recents."""
    agent, _ = agent_and_key
    agent.status = AgentStatus.ONLINE

    # Two sessions in different states.
    executing = Session(
        project_id=project.id,
        agent_id=agent.id,
        title="Executing run",
        state=SessionState.EXECUTING,
        progress_pct=50,
    )
    completed = Session(
        project_id=project.id,
        agent_id=agent.id,
        title="Completed run",
        state=SessionState.COMPLETED,
        progress_pct=100,
    )
    db_session.add_all([executing, completed])
    await db_session.flush()

    # A categorized doc reference (counts toward documents total).
    ref = GDriveReference(
        gdrive_file_id="file-1",
        file_name="readme.md",
        category=DocCategory.OVERVIEW,
    )
    # An uncategorized reference (must NOT count).
    plain_ref = GDriveReference(gdrive_file_id="file-2", file_name="scratch.md")
    db_session.add_all([ref, plain_ref])
    await db_session.flush()

    now = datetime.now(UTC)
    # Two commits today (one PLAN, one DOC) plus one older-but-in-window commit.
    db_session.add_all(
        [
            Commit(
                session_id=executing.id,
                agent_id=agent.id,
                type=CommitType.PLAN,
                message="plan",
                created_at=now,
            ),
            Commit(
                session_id=executing.id,
                agent_id=agent.id,
                type=CommitType.DOC,
                message="doc",
                gdrive_ref_id=ref.id,
                created_at=now,
            ),
            Commit(
                session_id=completed.id,
                agent_id=agent.id,
                type=CommitType.DOC,
                message="older doc",
                created_at=now - timedelta(days=3),
            ),
        ]
    )
    await db_session.commit()

    resp = await client.get("/api/v1/stats/overview")
    assert resp.status_code == 200
    body = resp.json()

    # Totals.
    assert body["totals"] == {
        "projects": 1,
        "sessions": 2,
        "agents": 1,
        "commits": 3,
        "documents": 1,  # only the categorized reference
    }

    # Sessions by state.
    states = {row["state"]: row["count"] for row in body["sessions_by_state"]}
    assert states == {"EXECUTING": 1, "COMPLETED": 1}

    # Agents by status.
    statuses = {row["status"]: row["count"] for row in body["agents_by_status"]}
    assert statuses == {"ONLINE": 1}

    # Commits by type.
    types = {row["type"]: row["count"] for row in body["commits_by_type"]}
    assert types == {"PLAN": 1, "DOC": 2}

    # Activity: exactly 14 zero-filled entries; today has 2 commits.
    activity = body["activity"]
    assert len(activity) == 14
    today = now.date().isoformat()
    by_date = {pt["date"]: pt["commits"] for pt in activity}
    assert by_date[today] == 2
    three_days_ago = (now - timedelta(days=3)).date().isoformat()
    assert by_date[three_days_ago] == 1
    assert sum(pt["commits"] for pt in activity) == 3

    # Recent sessions: most recent first, includes both seeded sessions.
    recent = body["recent_sessions"]
    assert len(recent) == 2
    recent_ids = {s["id"] for s in recent}
    assert recent_ids == {executing.id, completed.id}
    assert set(recent[0].keys()) == {
        "id",
        "title",
        "project_id",
        "state",
        "progress_pct",
        "started_at",
    }
