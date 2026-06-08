"""Tests for agent registration and using a minted key to check in."""

import pytest
from httpx import AsyncClient

from app.models.project import Project


@pytest.mark.asyncio
async def test_register_returns_key_once_and_can_check_in(
    client: AsyncClient, project: Project
) -> None:
    """Registering yields a one-time API key that authenticates a check-in."""
    reg = await client.post("/api/v1/agents", json={"name": "deploy-agent"})
    assert reg.status_code == 201
    body = reg.json()
    assert body["api_key"]  # plaintext key returned exactly once
    assert body["status"] == "OFFLINE"
    agent_id, api_key = body["id"], body["api_key"]

    # The minted key authenticates a real check-in.
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": api_key},
        json={"agent_id": agent_id, "project_id": project.id},
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == "INIT"


@pytest.mark.asyncio
async def test_revoked_agent_cannot_check_in(client: AsyncClient, project: Project) -> None:
    """After revocation the minted key is rejected with 401."""
    reg = await client.post("/api/v1/agents", json={"name": "temp-agent"})
    agent_id, api_key = reg.json()["id"], reg.json()["api_key"]

    revoke = await client.request("DELETE", f"/api/v1/agents/{agent_id}")
    assert revoke.status_code == 204

    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": api_key},
        json={"agent_id": agent_id, "project_id": project.id},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_agents_excludes_key_material(client: AsyncClient) -> None:
    """The agent list never exposes key hashes or plaintext keys."""
    await client.post("/api/v1/agents", json={"name": "a1"})
    listing = await client.get("/api/v1/agents")
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert "api_key" not in rows[0]
    assert "api_key_hash" not in rows[0]
