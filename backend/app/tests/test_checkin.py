"""Tests for the agent check-in endpoint."""

import pytest
from httpx import AsyncClient

from app.models.agent import Agent
from app.models.project import Project


@pytest.mark.asyncio
async def test_checkin_success(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """A valid key + matching agent_id returns a session and project context."""
    agent, api_key = agent_and_key
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": api_key},
        json={"agent_id": agent.id, "project_id": project.id, "capabilities": ["planning"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "INIT"
    assert body["project"]["gdrive_folder_id"] == "folder-123"
    assert body["session_id"]
    assert body["context"]["pending_feedback"] == []


@pytest.mark.asyncio
async def test_checkin_bad_key(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """An invalid API key is rejected with 401."""
    agent, _ = agent_and_key
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": "not-a-real-key"},
        json={"agent_id": agent.id, "project_id": project.id},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_checkin_unknown_project(
    client: AsyncClient, agent_and_key: tuple[Agent, str]
) -> None:
    """Checking in against a missing project returns 404."""
    agent, api_key = agent_and_key
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": api_key},
        json={"agent_id": agent.id, "project_id": "missing"},
    )
    assert resp.status_code == 404
