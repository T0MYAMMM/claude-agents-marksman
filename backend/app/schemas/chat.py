"""Pydantic models for the Markdown-editing chat assistant."""

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single turn in the chat conversation."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """A chat request: the conversation so far plus the document under edit."""

    messages: list[ChatMessage]
    current_markdown: str


class ChatResponse(BaseModel):
    """The assistant's reply, plus a full revised document when changes were requested."""

    reply: str
    revised_markdown: str | None = None
