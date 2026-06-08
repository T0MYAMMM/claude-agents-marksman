---
type: documentation
project: AI Agent Orchestration & Artifact Management System
generated_by: documentation agent
version: 1.0
---

# AI Agent Orchestration & Artifact Management System

A centralized dashboard and repository that tracks the plans, progress, and outputs of
multiple AI agents working on software tasks. Agents communicate over a private Tailscale
network; artifacts are Markdown stored in Google Drive; a relational database holds only
metadata and a Git-style commit log.

## Overview

The system coordinates AI agents through a strict operational protocol — check in, plan,
get human approval, execute in stages, and complete — while persisting every action as an
immutable commit and every artifact as a Markdown file in Drive. A Next.js dashboard lets
humans watch progress, inject feedback, approve plans, and read rendered artifacts.

Design principles: artifact bodies never live in the database (only references); commits
are append-only; networking is private by default (Tailscale, no public ports); and all
agent-generated Markdown carries YAML frontmatter for routing.

## Architecture

```
                         Tailscale tailnet (private, TLS)
 agents ───────────────▶ https://<node>.ts.net/        → backend API (FastAPI)
 humans (dashboard) ───▶ https://<node>.ts.net:8443/   → frontend (Next.js)

 backend ──▶ Neon Postgres   (metadata, sessions, commit log — never file bodies)
 backend ──▶ Google Drive    (Markdown artifacts, via OAuth user credentials)
```

- **Backend** — FastAPI + async SQLAlchemy 2.0 + Alembic; Pydantic v2 contracts.
- **Frontend** — Next.js App Router + TailwindCSS; server components + server actions.
- **Database** — PostgreSQL (Neon in production, SQLite for tests) via portable models.
- **File storage** — Google Drive; the DB stores only `gdrive_file_id` references.
- **Networking** — Tailscale `serve` exposes the stack tailnet-only (no public Funnel).

## Repository layout

```
backend/          FastAPI service
  app/
    api/v1/        routers: agents, sessions, webhooks, commits, projects, artifacts
    core/          auth (Tailscale + Argon2), security, pagination
    models/        Agent, Project, Session, Commit, GDriveReference, Feedback
    schemas/       Pydantic request/response contracts
    services/      gdrive (OAuth + backoff), version_control, session_state, artifact
    tests/         pytest-asyncio suite
  scripts/         gdrive_oauth (consent flow), verify_gdrive
  alembic/         migrations
frontend/         Next.js dashboard (src/app, src/components, src/lib)
packages/agent-sdk/  stdlib-only client SDK (AdminClient, AgentClient)
examples/         full_workflow.py, document_project.py
docs/             this documentation
```

## Data model

Six tables. IDs are application-generated UUID hex strings; timestamps are timezone-aware.

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `agents` | Registered AI workers | `name`, `api_key_hash` (Argon2), `status`, `tailscale_node` |
| `projects` | Workspaces | `name`, `gdrive_folder_id`, `description` |
| `sessions` | One agent run | `project_id`, `agent_id`, `state`, `progress_pct` |
| `commits` | Append-only log | `session_id`, `type`, `message`, `parent_commit_id`, `gdrive_ref_id`, `payload` |
| `gdrive_references` | Drive pointers | `gdrive_file_id`, `file_name`, `web_view_link`, `drive_revision_id` |
| `feedback` | Human review comments | `session_id`, `commit_id`, `comment`, `resolved` |

Commits form a self-referential tree via `parent_commit_id`, giving the Git-style timeline
for free. A keyset index on `(session_id, created_at)` keeps the timeline fast at depth.

## Agent operational protocol

A session moves through a state machine; `EXECUTING` is reachable only after a human
approves the plan.

```
INIT → PLANNING → WAITING_FOR_HUMAN ⇄ REFINING
                        │
                        ▼ (approve)
                   EXECUTING → COMPLETED
       (FAILED / TERMINATED reachable from active states)
```

1. **INIT** — agent checks in, authenticates, receives project context + pending feedback.
2. **PLANNING** — agent uploads a Markdown plan to Drive → `WAITING_FOR_HUMAN`.
3. **REFINEMENT** — human submits feedback → `REFINING`; agent uploads a revision,
   resolving the feedback → back to `WAITING_FOR_HUMAN`.
4. **APPROVAL** — human approves → `EXECUTING`.
5. **EXECUTION** — agent reports each stage; the session stays `EXECUTING`.
6. **COMPLETION** — agent uploads the final artifact → `COMPLETED`.

## API reference

All paths are prefixed `/api/v1`. Agent endpoints require the `X-Agent-Key` header;
human/admin endpoints are guarded by the Tailscale network check.

| Method | Path | Role | Purpose |
|--------|------|------|---------|
| POST | `/agents` | admin | Register an agent; returns the API key once |
| GET | `/agents` | admin | List agents (no key material) |
| DELETE | `/agents/{id}` | admin | Revoke an agent (soft delete) |
| POST | `/agents/checkin` | agent | INIT check-in |
| POST | `/sessions/{id}/plan` | agent | Upload plan |
| POST | `/sessions/{id}/refine` | agent | Upload revision |
| POST | `/sessions/{id}/feedback` | human | Inject feedback |
| POST | `/sessions/{id}/approve` | human | Approve plan |
| POST | `/sessions/{id}/complete` | agent | Upload final artifact |
| POST | `/webhooks/stage-report` | agent | Report stage progress |
| GET | `/sessions/{id}/commits` | any | Paginated commit timeline |
| GET | `/artifacts/{file_id}` | any | Fetch artifact content from Drive |
| CRUD | `/projects` | any | Project management |

## Storage: Google Drive

Artifacts are Markdown files in Drive; the DB stores only references. All Drive calls
retry with exponential backoff (tenacity) and map transient 429/5xx errors to a retryable
error type.

**Credential resolution** (in `services/gdrive.py`): OAuth user token → service-account
file → service-account inline JSON. A service account has **no storage quota on a personal
Google Drive**, so OAuth user credentials are required there; the app then writes as the
user. The least-privilege `drive.file` scope is used (the app only touches files it
creates). Authorize once with `scripts/gdrive_oauth.py`; the refresh token is persisted and
auto-refreshed.

## Networking: Tailscale

The backend is published only on loopback and exposed to the tailnet via `tailscale serve`
(tailnet-only, never public Funnel). The app-layer guard trusts the Tailscale CGNAT range
plus the Docker bridge (so the containerised frontend's server-side calls are allowed); the
real agent gate is the per-agent Argon2 API key.

## Deployment

Docker Compose runs backend + frontend; the database is external (Neon Postgres). The
backend applies `alembic upgrade head` on startup. Neon connection strings are normalized
in `config.py` (coerced to `asyncpg`, libpq-only params like `sslmode`/`channel_binding`
stripped, SSL re-applied via connect args). The backend listens on `127.0.0.1:8000`; the
frontend on `3001`; `tailscale serve` maps `:443`→backend and `:8443`→frontend.

## Frontend

Next.js App Router with four surfaces: the project **Dashboard** (grid), **Project detail**
(sessions with state badges + progress bars), the **Session/Topic Manager** (feedback
injection via server actions, approval, commit timeline), and the **Artifact Viewer**
(`react-markdown` with GFM, syntax highlighting, and an auto-generated table of contents).
API calls happen server-side, so the browser never talks to the backend directly.

## Agent SDK

`packages/agent-sdk` is a stdlib-only client (no third-party deps for agents). `AdminClient`
covers operator actions (register/revoke agents, create projects, inject feedback, approve);
`AgentClient` covers the protocol (check-in, plan, refine, report, complete). The `protocol`
module provides `markdown_document` (YAML frontmatter + H1) and `stage_payload` builders.

## Testing

A pytest-asyncio suite runs against in-memory SQLite with a `FakeGDrive` override, covering
check-in, the full protocol lifecycle, commit chaining, the session state machine,
credential resolution, and agent registration/revocation. Linting via ruff; all green.

## Known follow-ups

- Live dashboard updates (polling/SSE) — pages currently fetch on load.
- Infinite-scroll on the commit timeline (backend keyset pagination is ready).
- Optional Workspace Shared Drive support as an alternative to OAuth.
