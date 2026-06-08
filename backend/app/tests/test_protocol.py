"""End-to-end test of the agent operational protocol (plan -> complete)."""

import pytest
from httpx import AsyncClient

from app.models.agent import Agent
from app.models.project import Project


async def _checkin(client: AsyncClient, agent: Agent, api_key: str, project: Project) -> str:
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": api_key},
        json={"agent_id": agent.id, "project_id": project.id},
    )
    return resp.json()["session_id"]


def _artifact(agent_id: str, name: str) -> dict:
    return {
        "agent_id": agent_id,
        "file_name": name,
        "content": f"---\ntype: plan\n---\n# {name}\n",
        "commit_message": f"upload {name}",
    }


@pytest.mark.asyncio
async def test_full_protocol_flow(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project, fake_gdrive
) -> None:
    """Plan -> feedback -> refine -> approve -> stage report -> complete."""
    agent, api_key = agent_and_key
    h = {"X-Agent-Key": api_key}
    sid = await _checkin(client, agent, api_key, project)

    # PLANNING -> WAITING_FOR_HUMAN
    plan = await client.post(
        f"/api/v1/sessions/{sid}/plan", headers=h, json=_artifact(agent.id, "plan.md")
    )
    assert plan.status_code == 201
    assert plan.json()["session_state"] == "WAITING_FOR_HUMAN"
    assert plan.json()["gdrive_file_id"] == "drive-file-1"
    assert len(fake_gdrive.uploads) == 1

    # Human feedback -> REFINING
    fb = await client.post(
        f"/api/v1/sessions/{sid}/feedback", json={"comment": "Add error handling"}
    )
    assert fb.status_code == 201
    assert fb.json()["resolved"] is False

    # Re-check-in surfaces the pending feedback
    ctx = await client.post(
        "/api/v1/agents/checkin",
        headers=h,
        json={"agent_id": agent.id, "project_id": project.id},
    )
    pending = ctx.json()["context"]["pending_feedback"]
    assert any(p["comment"] == "Add error handling" for p in pending)

    # REFINEMENT -> WAITING_FOR_HUMAN, feedback resolved
    rev = await client.post(
        f"/api/v1/sessions/{sid}/refine", headers=h, json=_artifact(agent.id, "plan-v2.md")
    )
    assert rev.status_code == 201
    assert rev.json()["session_state"] == "WAITING_FOR_HUMAN"
    resolved = await client.get(f"/api/v1/sessions/{sid}/feedback")
    assert all(f["resolved"] for f in resolved.json())

    # Approve -> EXECUTING
    appr = await client.post(f"/api/v1/sessions/{sid}/approve")
    assert appr.status_code == 200
    assert appr.json()["session_state"] == "EXECUTING"

    # Stage report stays EXECUTING
    stage = await client.post(
        "/api/v1/webhooks/stage-report",
        headers=h,
        json={
            "session_id": sid,
            "agent_id": agent.id,
            "stage": {"index": 1, "name": "build", "of_total": 2},
            "progress_pct": 50,
            "commit_message": "halfway",
        },
    )
    assert stage.status_code == 201

    # COMPLETION -> COMPLETED at 100%
    done = await client.post(
        f"/api/v1/sessions/{sid}/complete", headers=h, json=_artifact(agent.id, "final.md")
    )
    assert done.status_code == 201
    assert done.json()["session_state"] == "COMPLETED"

    # Timeline holds the full chain: plan, revision, stage report, completion
    page = await client.get(f"/api/v1/sessions/{sid}/commits")
    types = [c["type"] for c in page.json()["items"]]
    assert types == ["COMPLETION", "STAGE_REPORT", "REVISION", "PLAN"]


@pytest.mark.asyncio
async def test_approve_requires_waiting_state(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """Approving a session that has no plan yet (INIT) is a 409 conflict."""
    agent, api_key = agent_and_key
    sid = await _checkin(client, agent, api_key, project)
    resp = await client.post(f"/api/v1/sessions/{sid}/approve")
    assert resp.status_code == 409
