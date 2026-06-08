"""Document a sample project into the orchestration system's bookshelf.

Demonstrates the full bookshelf workflow via the SDK: register a docs agent → create a
project → provision the bookshelf (project folder + 6 category subfolders) → check in →
upload one representative Markdown book to EACH of the 6 categories → read the library
back and print the shelf grouped by category.

Usage:
    python examples/document_to_bookshelf.py \
        --base-url https://<node>.<tailnet>.ts.net/api/v1 \
        --folder-id <parent_drive_folder_id> \
        --project-name "Sample Project Docs" \
        [--cleanup]

The parent --folder-id defaults to a shared demo folder. Point --base-url and --folder-id
at your own deployment to publish a real shelf.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "agent-sdk"))

from orchestrator_sdk import (  # noqa: E402
    AdminClient,
    AgentClient,
    OrchestratorError,
    markdown_document,
)

DEFAULT_FOLDER = "1s2uz-M0R9otOKQpaNZ9X6KFhuUwTqJ0_"

CATEGORIES = ("overview", "architecture", "guides", "tutorials", "reference", "rules")

# One representative book per category. Each (file_name, title, body) is rendered with
# proper YAML frontmatter via protocol.markdown_document before upload.
SAMPLE_BOOKS: dict[str, tuple[str, str, str]] = {
    "overview": (
        "overview.md",
        "Sample Project — Overview",
        "## What it is\n\nA tiny demo service that echoes greetings.\n\n"
        "## Why it exists\n\nTo show the bookshelf end to end.\n\n"
        "## Quickstart\n\n```bash\npython app.py --name World\n```\n\n"
        "## Status\n\nDemo-quality; not for production.\n",
    ),
    "architecture": (
        "architecture.md",
        "Sample Project — Architecture",
        "## Components\n\nA CLI front end calling a single greeting function.\n\n"
        "## Data flow\n\n```mermaid\nflowchart LR\n    U[User] --> CLI[app.py]\n"
        "    CLI --> G[greet()]\n    G --> CLI\n    CLI --> U\n```\n\n"
        "## Tech stack\n\nPython standard library only.\n\n"
        "## Key decisions\n\nStdlib-only to keep the demo dependency-free.\n",
    ),
    "guides": (
        "setup.md",
        "Guide — Setup",
        "## Prerequisites\n\nPython 3.11+.\n\n"
        "## Steps\n\n```bash\ngit clone <repo>\npython app.py --name Ada\n```\n\n"
        "See the [overview](../overview/overview.md) for the bigger picture.\n",
    ),
    "tutorials": (
        "first-greeting.md",
        "Tutorial — Your First Greeting",
        "## Goal\n\nProduce your first greeting from a clean checkout.\n\n"
        "## Walkthrough\n\n1. Clone the repo.\n2. Run `python app.py --name You`.\n"
        "3. Observe the printed greeting.\n\nYou have now run the project end to end.\n",
    ),
    "reference": (
        "cli-app.md",
        "Reference — app.py CLI",
        "## Synopsis\n\n```bash\napp.py --name NAME\n```\n\n"
        "## Arguments\n\n| Flag | Required | Description |\n"
        "| --- | --- | --- |\n| `--name` | yes | Who to greet. |\n\n"
        "## Output\n\nPrints `Hello, NAME!` to stdout.\n",
    ),
    "rules": (
        "conventions.md",
        "Rules — Conventions",
        "## Coding standards\n\nType hints and docstrings on all functions; format with"
        " `ruff`.\n\n## Do / Don't\n\n- Do keep the demo dependency-free.\n"
        "- Don't add network calls.\n",
    ),
}


def step(n: int, title: str) -> None:
    print(f"\n\033[1;36m[{n}]\033[0m {title}")


def build_book(category: str, file_name: str, title: str, body: str) -> str:
    """Render a category book with standards-compliant frontmatter."""
    return markdown_document(
        title,
        {
            "type": "reference" if category == "reference" else category,
            "category": category,
            "version": "1.0",
            "source_path": f"{category}/{file_name}",
        },
        body,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    ap.add_argument("--folder-id", default=DEFAULT_FOLDER, help="Parent Drive folder ID")
    ap.add_argument("--project-name", default="Sample Project Docs")
    ap.add_argument("--cleanup", action="store_true", help="Delete the project at the end")
    args = ap.parse_args()

    title = args.project_name
    print(f"Documenting '{title}' into a bookshelf under Drive folder {args.folder_id}")

    admin = AdminClient(args.base_url)

    step(1, "Register a documentation agent")
    reg = admin.register_agent("docs-agent", tailscale_node="docs.tailnet.ts.net")
    agent = AgentClient(args.base_url, reg["id"], reg["api_key"])
    print(f"    agent_id={reg['id']}")

    step(2, "Create the project (parent Drive folder)")
    project = admin.create_project(
        title, gdrive_folder_id=args.folder_id, description=f"Bookshelf demo for {title}"
    )
    pid = project["id"]
    print(f"    project_id={pid}  parent_folder={args.folder_id}")

    step(3, "Provision the bookshelf (folder + 6 category subfolders)")
    shelf = admin.provision_bookshelf(pid)
    print(f"    bookshelf_folder_id={shelf.get('bookshelf_folder_id')}")

    step(4, "Check in")
    sid = agent.check_in(pid)["session_id"]
    print(f"    session_id={sid}")

    step(5, "Upload one book to each of the 6 categories")
    for category in CATEGORIES:
        file_name, book_title, body = SAMPLE_BOOKS[category]
        content = build_book(category, file_name, book_title, body)
        result = agent.document(
            sid, category, file_name, content, f"Document {category}: {book_title}"
        )
        print(f"    {category:<13} {file_name:<22} → drive_file={result.get('gdrive_file_id')}")

    step(6, "Read the library back and print the shelf")
    library = admin.list_library(pid)
    print(f"    bookshelf_folder_id={library.get('bookshelf_folder_id')}")
    for section in library.get("sections", []):
        docs = section.get("documents", [])
        print(f"\n    \033[1m{section['category']}\033[0m ({len(docs)})")
        for doc in docs:
            print(f"      - {doc['file_name']}  ({doc['gdrive_file_id']})")

    if args.cleanup:
        admin.delete_project(pid)
        print("\n    cleaned up project")
    else:
        host = args.base_url.split("/api/")[0].replace(":8000", "")
        print("\n\033[1;32mBookshelf published.\033[0m")
        print(f"    dashboard: {host}  → project '{title}'")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OrchestratorError as exc:
        print(f"\n\033[1;31mAPI error\033[0m {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
