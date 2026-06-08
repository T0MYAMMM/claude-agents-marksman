---
type: runbook
title: Documenting an existing project with the orchestration system
version: 1.0
---

# Documenting an existing project with the orchestration system

This runbook produces a full Markdown document explaining an existing project, versioned
through the agent protocol and stored in Google Drive, viewable in the dashboard. It uses
the system the way a real documentation agent would: plan → (review) → approve → write
section by section → complete.

The reference implementation is `examples/document_project.py`, which drives every step via
the SDK. You can run it end-to-end, or follow the manual steps to understand each phase.

## Prerequisites

- The stack is deployed and reachable (locally `http://127.0.0.1:8000/api/v1`, or over the
  tailnet `https://<node>.ts.net/api/v1`).
- Google Drive is authorized (OAuth token in place) and you have a target **Drive folder
  ID** to store artifacts.
- A finished Markdown document for the project (the content to publish). Authoring the
  content is the "intelligence" step — an AI agent writes it by analyzing the codebase;
  `examples/document_project.py` takes that finished file as input.

## The steps

### 1. Write the documentation (the agent's job)

Analyze the project and produce one Markdown file with **YAML frontmatter** and `##`
section headers — Overview, Architecture, Data model, API, Deployment, etc. Each `##`
section becomes a reported stage, so structure the document the way you want progress to
read. See `docs/orchestration-system.md` for a complete example.

### 2. Register a documentation agent

```
POST /api/v1/agents   {"name": "docs-agent"}      → returns a one-time api_key
```
Store the key; it is shown once. (Or reuse an existing agent's key.)

### 3. Create or choose a project workspace

```
POST /api/v1/projects {"name": "<Project> Docs", "gdrive_folder_id": "<folder>"}
```
The `gdrive_folder_id` is where the Markdown artifacts will be written.

### 4. Check in

```
POST /api/v1/agents/checkin  {"agent_id": "...", "project_id": "..."}   → session_id
```

### 5. Submit a documentation plan

Upload an **outline** (the section list) as the plan. This is the contract a human reviews
before the full document is written.
```
POST /api/v1/sessions/{id}/plan   { file_name: "docs-plan.md", content: "<outline>", ... }
```
Session → `WAITING_FOR_HUMAN`.

### 6. (Optional) Review and refine

A reviewer can inject feedback on the outline:
```
POST /api/v1/sessions/{id}/feedback  {"comment": "Add a security section"}
```
The agent re-checks-in (sees the feedback), revises the outline, and re-submits:
```
POST /api/v1/sessions/{id}/refine    { file_name: "docs-plan-v2.md", ... }
```

### 7. Approve the plan

```
POST /api/v1/sessions/{id}/approve            Session → EXECUTING
```

### 8. Write section by section, reporting progress

For each `##` section, report a stage so the dashboard progress bar advances:
```
POST /api/v1/webhooks/stage-report
  { stage: {index, name: "<section>", of_total: N}, progress_pct, completed_tasks, ... }
```

### 9. Complete with the full document

Upload the assembled Markdown as the final artifact:
```
POST /api/v1/sessions/{id}/complete  { file_name: "<project>-documentation.md", content, ... }
```
Session → `COMPLETED`. The full document now lives in Drive.

### 10. View it

- **Dashboard** → the project → the session: see the state, progress, and Git-style
  commit timeline (plan → revision → one commit per section → completion).
- **Artifact Viewer** → renders the Markdown with a table of contents and syntax
  highlighting, fetched from Drive via `GET /api/v1/artifacts/{file_id}`.

## One-command version

```
python examples/document_project.py \
  --doc docs/orchestration-system.md \
  --project-name "Orchestration System Docs" \
  --folder-id <your_drive_folder_id> \
  --base-url https://<node>.ts.net/api/v1 \
  [--with-review]   # also demos the feedback → refine cycle
```

It derives the outline and per-section stages from the document's `##` headers, runs the
full protocol, and prints the dashboard links. To document a different project, point
`--doc` at that project's Markdown and pick its `--project-name` / `--folder-id`.
