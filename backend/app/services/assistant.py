"""Claude-powered Markdown editing assistant.

The actual Anthropic call sits behind the module-level ``_complete`` seam so tests can
monkeypatch it without a network call. ``edit_chat`` builds the system prompt, maps the
conversation, runs the (synchronous) SDK call in a threadpool, and parses the response.
"""

import re

from anthropic import Anthropic

from app.config import get_settings
from app.schemas.chat import ChatMessage

# Sonnet-tier model: fast and capable, well-suited to an interactive editing assistant.
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 8192

_SYSTEM_PROMPT = (
    "You are a documentation editing assistant. You help the user improve a Markdown "
    "document. The CURRENT DOCUMENT is provided to you for context. Reply helpfully and "
    "conversationally. When — and only when — the user requests changes to the document, "
    "include the COMPLETE revised document in a single fenced ```markdown ... ``` code "
    "block. Do not include a markdown code block if the user is only asking a question or "
    "no changes are needed. When you do revise, always emit the entire document, not just "
    "the changed portion."
)

# Matches the first ```markdown ... ``` fenced block (case-insensitive language tag).
_MARKDOWN_BLOCK = re.compile(r"```markdown[ \t]*\n(.*?)\n?```", re.DOTALL | re.IGNORECASE)


def _complete(system: str, messages: list[dict[str, str]]) -> str:
    """Call Anthropic's Messages API and return the assistant's text.

    This is the injectable seam: tests monkeypatch this function to avoid a real
    network call. Runs synchronously; callers should invoke it via to_thread.run_sync.
    """
    client = Anthropic(api_key=get_settings().anthropic_api_key)
    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=system,
        messages=messages,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _parse(text: str) -> tuple[str, str | None]:
    """Split a raw completion into (reply, revised_markdown).

    Extracts the first fenced ```markdown block as the revised document (stripped) and
    returns the remaining text as the reply. If no fenced markdown block is present,
    revised_markdown is None and the whole text is the reply.
    """
    match = _MARKDOWN_BLOCK.search(text)
    if match is None:
        return text.strip(), None
    revised = match.group(1).strip()
    reply = (text[: match.start()] + text[match.end() :]).strip()
    return reply, revised


async def edit_chat(
    messages: list[ChatMessage], current_markdown: str
) -> tuple[str, str | None]:
    """Run an editing-assistant turn; return (reply, revised_markdown).

    Maps the conversation to the Anthropic message format, appends a final user context
    block carrying the current document, and parses the response for a revised document.
    """
    from anyio import to_thread

    api_messages: list[dict[str, str]] = [
        {"role": m.role, "content": m.content} for m in messages
    ]
    api_messages.append(
        {
            "role": "user",
            "content": (
                "CURRENT DOCUMENT (the Markdown you are editing):\n\n"
                f"```markdown\n{current_markdown}\n```"
            ),
        }
    )
    raw = await to_thread.run_sync(_complete, _SYSTEM_PROMPT, api_messages)
    return _parse(raw)
