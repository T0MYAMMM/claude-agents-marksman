"""Chat endpoint: a Claude-powered Markdown editing assistant.

Gated on APP_ANTHROPIC_API_KEY — when unset, the endpoint returns 503. The document
being edited is supplied in the request body, so no Drive fetch happens here; the path
file ID exists only to give the chat a clean, artifact-scoped URL.
"""

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.assistant import edit_chat

router = APIRouter(prefix="/artifacts", tags=["chat"])


@router.post("/{gdrive_file_id}/chat", response_model=ChatResponse)
async def chat(gdrive_file_id: str, body: ChatRequest) -> ChatResponse:
    """Send a chat turn to the editing assistant for the given artifact."""
    if not get_settings().anthropic_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Chat assistant not configured (set APP_ANTHROPIC_API_KEY)",
        )
    reply, revised_markdown = await edit_chat(body.messages, body.current_markdown)
    return ChatResponse(reply=reply, revised_markdown=revised_markdown)
