"""Document an existing project through the orchestration system.

Takes a finished Markdown document and versions it through the agent protocol: register →
check in → plan (outline) → [review → refine] → approve → one stage per section → complete.
The full document lands in Google Drive and the dashboard, with a Git-style commit timeline.

Usage:
    python examples/document_project.py \
        --doc docs/orchestration-system.md \
        --project-name "Orchestration System Docs" \
        --folder-id <drive_folder_id> \
        --base-url https://<node>.<tailnet>.ts.net/api/v1 \
        [--with-review] [--cleanup]

Section stages are derived from the document's `##` headers. Point --doc at any project's
Markdown to document a different project.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "agent-sdk"))

from orchestrator_sdk import (  # noqa: E402
    AdminClient,
    AgentClient,
    OrchestratorError,
    markdown_document,
    stage_payload,
)

DEFAULT_FOLDER = "1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_"


def step(n: int, title: str) -> None:
    print(f"\n\033[1;36m[{n}]\033[0m {title}")


def extract_sections(markdown: str) -> list[str]:
    """Return the `##` section titles, in order (these become the reported stages)."""
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", markdown, re.MULTILINE)]


def build_outline(title: str, sections: list[str], session_id: str) -> str:
    """Render a documentation plan (outline) from the section titles."""
    body = "## Documentation outline\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(sections, 1))
    return markdown_document(
        f"{title} — Documentation Plan",
        {"type": "plan", "session": session_id, "sections": len(sections)},
        body,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc", required=True, help="Path to the finished Markdown document")
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--folder-id", default=DEFAULT_FOLDER)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    ap.add_argument("--with-review", action="store_true", help="Also demo feedback → refine")
    ap.add_argument("--cleanup", action="store_true", help="Delete the project at the end")
    args = ap.parse_args()

    doc_path = Path(args.doc)
    document = doc_path.read_text()
    sections = extract_sections(document)
    if not sections:
        print("No `##` sections found in the document; nothing to stage.", file=sys.stderr)
        return 1
    title = args.project_name
    out_name = doc_path.stem + "-documentation.md"
    print(f"Documenting '{title}' from {doc_path} — {len(sections)} sections")

    admin = AdminClient(args.base_url)

    step(1, "Register a documentation agent")
    reg = admin.register_agent("docs-agent", tailscale_node="docs.tailnet.ts.net")
    agent = AgentClient(args.base_url, reg["id"], reg["api_key"])
    print(f"    agent_id={reg['id']}")

    step(2, "Create the documentation project")
    project = admin.create_project(title, gdrive_folder_id=args.folder_id, description=f"Docs for {title}")
    pid = project["id"]
    print(f"    project_id={pid}  drive_folder={args.folder_id}")

    step(3, "Check in")
    sid = agent.check_in(pid)["session_id"]
    print(f"    session_id={sid}")

    step(4, "Submit the documentation plan (outline → Drive)")
    outline = build_outline(title, sections, sid)
    pl = agent.submit_plan(sid, "docs-plan.md", outline, "Documentation outline")
    print(f"    plan drive_file={pl['gdrive_file_id']}  state={pl['session_state']}")

    if args.with_review:
        step(5, "Human review: request a tweak, agent refines the outline")
        admin.submit_feedback(sid, "Confirm the outline covers deployment and security.")
        ck = agent.check_in(pid)
        for f in ck["context"]["pending_feedback"]:
            print(f"    ↳ feedback: {f['comment']}")
        rev = agent.refine(sid, "docs-plan-v2.md", outline, "Outline reviewed; deployment + security present")
        print(f"    revision drive_file={rev['gdrive_file_id']}")

    step(6, "Approve the plan (→ EXECUTING)")
    print(f"    state={admin.approve(sid)['session_state']}")

    step(7, "Write section by section, reporting progress")
    total = len(sections)
    for i, name in enumerate(sections, start=1):
        pct = round(i / total * 100)
        r = agent.report_stage(
            sid,
            stage_payload(
                index=i, name=name, of_total=total, progress_pct=pct,
                completed_tasks=[f"Documented: {name}"],
                status="DONE" if i == total else "IN_PROGRESS",
                commit_message=f"Section {i}/{total}: {name}",
            ),
        )
        print(f"    [{i}/{total}] {name:<28} → {r['progress_pct']}%")

    step(8, "Complete: upload the full document (→ COMPLETED)")
    final = agent.complete(sid, out_name, document, f"Full documentation for {title}")
    print(f"    document drive_file={final['gdrive_file_id']}  state={final['session_state']}")

    step(9, "Commit timeline")
    for c in admin.list_commits(sid)["items"]:
        print(f"    {c['type']:<13} {c['message']}")

    if args.cleanup:
        admin.delete_project(pid)
        print("\n    cleaned up project")
    else:
        host = args.base_url.split("/api/")[0].replace(":8000", "")
        print("\n\033[1;32mDocumentation published.\033[0m")
        print(f"    artifact (Drive id): {final['gdrive_file_id']}")
        print(f"    dashboard          : {host}  → project '{title}' → session {sid}")
        print(f"    artifact viewer    : {host}/artifacts/{final['gdrive_file_id']}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OrchestratorError as exc:
        print(f"\n\033[1;31mAPI error\033[0m {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
