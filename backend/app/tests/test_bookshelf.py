"""Tests for the project bookshelf (documentation library) feature."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project


async def _checkin(client: AsyncClient, agent: Agent, api_key: str, project: Project) -> str:
    resp = await client.post(
        "/api/v1/agents/checkin",
        headers={"X-Agent-Key": api_key},
        json={"agent_id": agent.id, "project_id": project.id},
    )
    return resp.json()["session_id"]


@pytest.mark.asyncio
async def test_provision_bookshelf_is_idempotent(
    client: AsyncClient, project: Project, fake_gdrive
) -> None:
    """POST /bookshelf provisions folders once and returns the same result on repeat."""
    first = await client.post(f"/api/v1/projects/{project.id}/bookshelf")
    assert first.status_code == 200
    assert first.json()["bookshelf_folder_id"] == f"root-{project.name}"
    assert fake_gdrive.ensure_bookshelf_calls == 1

    second = await client.post(f"/api/v1/projects/{project.id}/bookshelf")
    assert second.status_code == 200
    assert second.json()["bookshelf_folder_id"] == first.json()["bookshelf_folder_id"]
    # Idempotent: no second Drive provisioning call.
    assert fake_gdrive.ensure_bookshelf_calls == 1


@pytest.mark.asyncio
async def test_submit_document_stores_category(
    client: AsyncClient,
    agent_and_key: tuple[Agent, str],
    project: Project,
    db_session: AsyncSession,
) -> None:
    """POST /sessions/{id}/document files a doc under its category."""
    agent, api_key = agent_and_key
    h = {"X-Agent-Key": api_key}
    sid = await _checkin(client, agent, api_key, project)

    resp = await client.post(
        f"/api/v1/sessions/{sid}/document",
        headers=h,
        json={
            "agent_id": agent.id,
            "category": "reference",
            "file_name": "api.md",
            "content": "# API\n",
            "commit_message": "add api reference",
        },
    )
    assert resp.status_code == 201

    refs = list((await db_session.execute(select(GDriveReference))).scalars())
    assert len(refs) == 1
    assert refs[0].category == "reference"


@pytest.mark.asyncio
async def test_library_groups_by_category(
    client: AsyncClient, agent_and_key: tuple[Agent, str], project: Project
) -> None:
    """GET /library returns 6 category sections with the doc under 'reference'."""
    agent, api_key = agent_and_key
    h = {"X-Agent-Key": api_key}
    sid = await _checkin(client, agent, api_key, project)

    await client.post(
        f"/api/v1/sessions/{sid}/document",
        headers=h,
        json={
            "agent_id": agent.id,
            "category": "reference",
            "file_name": "api.md",
            "content": "# API\n",
            "commit_message": "add api reference",
        },
    )

    lib = await client.get(f"/api/v1/projects/{project.id}/library")
    assert lib.status_code == 200
    body = lib.json()
    sections = {s["category"]: s["documents"] for s in body["sections"]}
    assert set(sections) == {
        "overview",
        "architecture",
        "guides",
        "tutorials",
        "reference",
        "rules",
    }
    assert len(body["sections"]) == 6
    assert len(sections["reference"]) == 1
    assert sections["reference"][0]["file_name"] == "api.md"
    assert all(len(docs) == 0 for cat, docs in sections.items() if cat != "reference")
