"""Tests for artifact deletion and idempotent document upload (cleanup capabilities)."""

import pytest
from httpx import AsyncClient

from app.models.agent import Agent
from app.models.project import Project


async def _doc_session(client: AsyncClient, agent: Agent, api_key: str, project: Project) -> str:
    h = {"X-Agent-Key": api_key}
    resp = await client.post(
        "/api/v1/agents/checkin", headers=h,
        json={"agent_id": agent.id, "project_id": project.id},
    )
    return resp.json()["session_id"]


def _doc(agent_id: str, name: str, content: str) -> dict:
    return {
        "agent_id": agent_id, "category": "reference",
        "file_name": name, "content": content, "commit_message": f"doc {name}",
    }


@pytest.mark.asyncio
async def test_document_upload_is_idempotent_by_name(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project, fake_gdrive
) -> None:
    """Re-posting the same file_name updates in place instead of appending a duplicate."""
    agent, api_key = agent_and_key
    h = {"X-Agent-Key": api_key}
    sid = await _doc_session(client, agent, api_key, project)

    r1 = await client.post(f"/api/v1/sessions/{sid}/document", headers=h,
                           json=_doc(agent.id, "api.md", "# v1"))
    fid1 = r1.json()["gdrive_file_id"]
    r2 = await client.post(f"/api/v1/sessions/{sid}/document", headers=h,
                           json=_doc(agent.id, "api.md", "# v2"))
    fid2 = r2.json()["gdrive_file_id"]

    assert fid1 == fid2  # same Drive file reused, not a new one
    # The library shows exactly one 'reference' doc named api.md (no duplicate).
    lib = (await client.get(f"/api/v1/projects/{project.id}/library")).json()
    ref = next(s for s in lib["sections"] if s["category"] == "reference")
    assert [d["file_name"] for d in ref["documents"]] == ["api.md"]
    # The second call performed an in-place Drive update.
    assert any(u.get("updated") for u in fake_gdrive.uploads)


@pytest.mark.asyncio
async def test_delete_artifact_removes_from_shelf(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project, fake_gdrive
) -> None:
    """DELETE /artifacts/{id} trashes the Drive file and drops it from the library."""
    agent, api_key = agent_and_key
    h = {"X-Agent-Key": api_key}
    sid = await _doc_session(client, agent, api_key, project)
    fid = (await client.post(f"/api/v1/sessions/{sid}/document", headers=h,
                             json=_doc(agent.id, "junk.md", "# oops"))).json()["gdrive_file_id"]

    resp = await client.request("DELETE", f"/api/v1/artifacts/{fid}")
    assert resp.status_code == 204
    assert fid in fake_gdrive.trashed

    lib = (await client.get(f"/api/v1/projects/{project.id}/library")).json()
    names = [d["file_name"] for s in lib["sections"] for d in s["documents"]]
    assert "junk.md" not in names


@pytest.mark.asyncio
async def test_delete_unknown_is_idempotent(client: AsyncClient) -> None:
    """Deleting a file with no DB reference still succeeds (idempotent cleanup)."""
    resp = await client.request("DELETE", "/api/v1/artifacts/nonexistent-file-id")
    assert resp.status_code == 204
