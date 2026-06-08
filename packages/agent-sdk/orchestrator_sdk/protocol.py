"""Helpers for building protocol payloads and standards-compliant Markdown."""

from typing import Any


def markdown_document(title: str, frontmatter: dict[str, Any], body: str) -> str:
    """Render a Markdown doc with YAML frontmatter and an H1 title.

    Satisfies the project's Markdown standard: YAML frontmatter for metadata routing
    plus strict header formatting. Kept dependency-free with a minimal YAML emitter
    (flat scalar values only).
    """
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    return "\n".join(lines)


def _yaml_scalar(value: Any) -> str:
    """Emit a flat YAML scalar; quote strings containing special characters."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(c in text for c in ":#") or text != text.strip():
        return '"' + text.replace('"', '\\"') + '"'
    return text


def stage_payload(
    *,
    index: int,
    name: str,
    of_total: int,
    progress_pct: int,
    completed_tasks: list[str] | None = None,
    blockers: list[dict[str, str]] | None = None,
    minor_changes: list[str] | None = None,
    commit_message: str,
    status: str = "IN_PROGRESS",
    artifact: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a stage-report body for AgentClient.report_stage."""
    payload: dict[str, Any] = {
        "stage": {"index": index, "name": name, "of_total": of_total},
        "progress_pct": progress_pct,
        "status": status,
        "completed_tasks": completed_tasks or [],
        "blockers": blockers or [],
        "minor_changes": minor_changes or [],
        "commit_message": commit_message,
    }
    if artifact is not None:
        payload["artifact"] = artifact
    return payload
