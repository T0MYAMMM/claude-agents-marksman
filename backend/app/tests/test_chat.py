"""Tests for the artifact PATCH write-back and the Claude-powered chat endpoint.

No real network call is made: the Drive layer is the FakeGDrive fixture and the
Anthropic call is stubbed via the ``_complete`` seam in app.services.assistant.
"""

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.services import assistant


@pytest.fixture
def _reset_anthropic_key():
    """Snapshot and restore the Anthropic key setting around each test."""
    s = get_settings()
    saved = s.anthropic_api_key
    s.anthropic_api_key = ""
    yield s
    s.anthropic_api_key = saved


async def test_patch_artifact_updates_and_returns_revision(client: AsyncClient) -> None:
    """PATCH /artifacts/{id} writes via Drive and returns the new revision."""
    resp = await client.patch(
        "/api/v1/artifacts/file-xyz", json={"content": "# updated\n"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"gdrive_file_id": "file-xyz", "drive_revision_id": "rev-updated"}


async def test_chat_unconfigured_returns_503(
    client: AsyncClient, _reset_anthropic_key
) -> None:
    """With no Anthropic key set, the chat endpoint reports it is not configured."""
    _reset_anthropic_key.anthropic_api_key = ""
    resp = await client.post(
        "/api/v1/artifacts/file-xyz/chat",
        json={"messages": [{"role": "user", "content": "hi"}], "current_markdown": "# x\n"},
    )
    assert resp.status_code == 503
    assert "APP_ANTHROPIC_API_KEY" in resp.json()["detail"]


async def test_chat_extracts_revised_markdown(
    client: AsyncClient, _reset_anthropic_key, monkeypatch
) -> None:
    """A response with a fenced markdown block yields revised_markdown + a clean reply."""
    _reset_anthropic_key.anthropic_api_key = "test-key"
    canned = (
        "Sure, I added a heading.\n\n"
        "```markdown\n# New Title\n\nBody text.\n```\n\n"
        "Let me know if you want more."
    )
    monkeypatch.setattr(assistant, "_complete", lambda system, messages: canned)

    resp = await client.post(
        "/api/v1/artifacts/file-xyz/chat",
        json={
            "messages": [{"role": "user", "content": "add a heading"}],
            "current_markdown": "Body text.\n",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["revised_markdown"] == "# New Title\n\nBody text."
    assert "```markdown" not in body["reply"]
    assert "Sure, I added a heading." in body["reply"]
    assert "Let me know if you want more." in body["reply"]


async def test_chat_no_markdown_block_returns_none(
    client: AsyncClient, _reset_anthropic_key, monkeypatch
) -> None:
    """A response without a fenced markdown block leaves revised_markdown None."""
    _reset_anthropic_key.anthropic_api_key = "test-key"
    canned = "That document already looks good — no changes needed."
    monkeypatch.setattr(assistant, "_complete", lambda system, messages: canned)

    resp = await client.post(
        "/api/v1/artifacts/file-xyz/chat",
        json={
            "messages": [{"role": "user", "content": "anything to fix?"}],
            "current_markdown": "# Fine\n",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["revised_markdown"] is None
    assert body["reply"] == canned
