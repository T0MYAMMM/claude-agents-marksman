"""Tests for the stage-report webhook and resulting commit chaining."""

import pytest
from httpx import AsyncClient

from app.models.agent import Agent
from app.models.project import Project


async def _executing_session(
    client: AsyncClient, agent: Agent, api_key: str, project: Project
) -> str:
    """Check in, submit a plan, and approve it so the session reaches EXECUTING."""
    h = {"X-Agent-Key": api_key}
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers=h,
        json={"agent_id": agent.id, "project_id": project.id},
    )
    sid = resp.json()["session_id"]
    await client.post(
        f"/api/v1/sessions/{sid}/plan",
        headers=h,
        json={
            "agent_id": agent.id,
            "file_name": "plan.md",
            "content": "# plan\n",
            "commit_message": "plan",
        },
    )
    await client.post(f"/api/v1/sessions/{sid}/approve")
    return sid


def _stage_body(session_id: str, agent_id: str, pct: int, idx: int) -> dict:
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "stage": {"index": idx, "name": f"Stage {idx}", "of_total": 3},
        "progress_pct": pct,
        "status": "IN_PROGRESS",
        "completed_tasks": [f"task-{idx}"],
        "commit_message": f"Stage {idx} done",
    }


@pytest.mark.asyncio
async def test_stage_report_creates_commit_and_advances_progress(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """A stage report is accepted, returns 201, and advances session progress."""
    agent, api_key = agent_and_key
    session_id = await _executing_session(client, agent, api_key, project)

    resp = await client.post(
        "/api/v1/webhooks/stage-report",
        headers={"X-Agent-Key": api_key},
        json=_stage_body(session_id, agent.id, pct=33, idx=1),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["session_state"] == "EXECUTING"
    assert body["progress_pct"] == 33
    assert body["next_action"] == "CONTINUE"
    assert body["commit_id"]


@pytest.mark.asyncio
async def test_commits_chain_via_parent(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """Successive reports form a parent-linked chain, newest-first in the timeline."""
    agent, api_key = agent_and_key
    session_id = await _executing_session(client, agent, api_key, project)

    for idx, pct in enumerate([20, 60, 100], start=1):
        r = await client.post(
            "/api/v1/webhooks/stage-report",
            headers={"X-Agent-Key": api_key},
            json=_stage_body(session_id, agent.id, pct=pct, idx=idx),
        )
        assert r.status_code == 201

    page = await client.get(f"/api/v1/sessions/{session_id}/commits")
    items = page.json()["items"]
    # 3 stage reports chained onto the initial PLAN commit (4 total, newest first).
    assert len(items) == 4
    assert [c["type"] for c in items] == [
        "STAGE_REPORT",
        "STAGE_REPORT",
        "STAGE_REPORT",
        "PLAN",
    ]
    assert items[0]["parent_commit_id"] == items[1]["id"]
    assert items[1]["parent_commit_id"] == items[2]["id"]
    assert items[2]["parent_commit_id"] == items[3]["id"]  # first report chains to PLAN
    assert items[3]["parent_commit_id"] is None  # PLAN is the root


@pytest.mark.asyncio
async def test_stage_report_wrong_agent_forbidden(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """A report whose body agent_id mismatches the authenticated agent is rejected."""
    agent, api_key = agent_and_key
    session_id = await _executing_session(client, agent, api_key, project)
    body = _stage_body(session_id, "someone-else", pct=10, idx=1)
    resp = await client.post(
        "/api/v1/webhooks/stage-report", headers={"X-Agent-Key": api_key}, json=body
    )
    assert resp.status_code == 403
