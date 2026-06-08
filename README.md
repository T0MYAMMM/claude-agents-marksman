# AI Agent Orchestration & Artifact Management System

Centralized dashboard and repository tracking the plans, progress, and Markdown artifacts
of AI development agents. Agents check in over a private **Tailscale** network; artifacts
live in **Google Drive**; a relational DB holds metadata and a Git-style commit log.

## Architecture
```
┌─────────┐   Tailscale    ┌──────────────┐   GDrive API   ┌──────────────┐
│ Agents  │ ─────────────▶ │  FastAPI     │ ─────────────▶ │ Google Drive │
└─────────┘   API key      │  backend     │   (.md files)  └──────────────┘
                           │              │
┌─────────┐   Tailscale    │   SQLite /   │   metadata + commit log
│ Next.js │ ─────────────▶ │   Postgres   │
│ dashboard               └──────────────┘
└─────────┘
```
- **Backend** — FastAPI, SQLAlchemy async, Alembic, Argon2 auth, Tailscale CIDR guard,
  tenacity backoff for Drive. See [backend/README.md](backend/README.md).
- **Frontend** — Next.js App Router + TailwindCSS. Dashboard, session manager, artifact
  viewer (Markdown + ToC + syntax highlighting), Git-style commit timeline.
- **Storage** — artifact bodies in Drive; only references + commits in the DB.

## Quickstart (local)
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env
alembic upgrade head
uvicorn app.main:app --reload        # http://localhost:8000/docs

# Frontend (separate shell)
cd frontend
npm install
cp .env.example .env.local
npm run dev                          # http://localhost:3000
```

Or run the whole stack with `docker compose up -d` (backend + frontend; the backend runs
`alembic upgrade head` on startup). The DB is external (Neon Postgres) via `APP_DATABASE_URL`.

## Deploy on a VPS
The app is a self-contained Docker Compose stack (backend + frontend); the database is
external (any async-Postgres URL). Secrets and `backend/.env` are gitignored — you provide
them on the server.

```bash
git clone <this repo> && cd claude-agents-marksman

# 1. Config
cp backend/.env.example backend/.env        # set APP_DATABASE_URL, APP_TAILSCALE_CIDR, etc.

# 2. Secrets — put credentials in the gitignored ./secrets dir
mkdir -p secrets
#   - OAuth (personal Google account): run the consent flow on a machine with a browser,
#     then copy the produced token to ./secrets/oauth-token.json   (see "Google Drive auth")
#   - or a service-account key → ./secrets/gdrive-sa.json (Workspace Shared Drive only)

# 3. Run (migrations apply automatically on backend startup)
docker compose up -d --build
# frontend → http://<vps>:3000   (override port: FRONTEND_PORT=8080 docker compose up -d)
# backend  → 127.0.0.1:8000 only (private; put a reverse proxy / Tailscale in front)
```

Put **TLS + a domain** in front with a reverse proxy (Caddy/nginx) or **Tailscale serve**.
For a public, non-Tailscale deploy, set `APP_TAILSCALE_CIDR=` (empty) in `backend/.env` and
protect the human/dashboard routes with your proxy's auth — the per-agent API key still
gates agent endpoints. Then update the hardcoded base URLs in `prompts/*.md` and the
published guide to your domain.

## Live deployment (Docker + Tailscale)
The stack runs in Docker; the backend is published only on `127.0.0.1:8000` (never public)
and exposed to agents over the tailnet via **`tailscale serve`** (tailnet-only, not Funnel).

```
                         Tailscale tailnet (private, TLS)
 agents ───────────────▶ https://<node>.<tailnet>.ts.net/         → 127.0.0.1:8000  (backend API)
 humans (dashboard) ───▶ https://<node>.<tailnet>.ts.net:8443/    → 127.0.0.1:3001  (frontend)
```

On WSL2, Tailscale runs on the Windows host. Expose the services (run on the host, once):
```powershell
tailscale serve --bg --https=443  http://127.0.0.1:8000   # backend API for agents
tailscale serve --bg --https=8443 http://127.0.0.1:3001   # dashboard for humans
```
Agents then use base URL `https://<node>.<tailnet>.ts.net/api/v1`. The config persists
across reboots (as long as `tailscaled` and Docker Desktop start). Tear down with
`tailscale serve --https=443 off` (and `:8443 off`).

> Network-guard note: because the containerised frontend and the serve proxy reach the API
> from the Docker bridge (not a `100.64.x` tailnet IP), `APP_TAILSCALE_CIDR` trusts
> `100.64.0.0/10,172.16.0.0/12`. The real agent gate is the per-agent API key; the CIDR
> check is defense-in-depth.

## Google Drive auth (personal account → OAuth)
A service account has **no storage quota on a personal Google Drive**, so artifacts must
be written as the user via OAuth. One-time setup:
1. GCP → Credentials → **OAuth client ID** → **Desktop app**; download `oauth-client.json`.
2. Authorize once (writes a refresh token to the repo-local, gitignored `./secrets`):
   ```bash
   cd backend && source .venv/bin/activate
   python -m scripts.gdrive_oauth \
     --client-secret /secrets/oauth-client.json \
     --token "$(pwd)/../secrets/oauth-token.json"
   ```
3. The backend (compose) already sets `APP_GDRIVE_OAUTH_TOKEN_PATH=/app/secrets/oauth-token.json`
   and mounts `./secrets`. Restart: `docker compose up -d backend`.

(On a Workspace account you can instead use a Shared Drive + the service account.)

## End-to-end example
`examples/full_workflow.py` exercises every feature against a live deployment and leaves
the dashboard populated:
```bash
python examples/full_workflow.py \
  --base-url https://<node>.<tailnet>.ts.net/api/v1 \
  --folder-id <your_drive_folder_id> [--revoke] [--cleanup]
```
It registers an agent, creates a project, then runs check-in → plan → feedback → refine →
approve → stage reports → complete, reads back the commit timeline and a Drive artifact,
and (with `--revoke`) demonstrates key revocation. Built on the stdlib-only
`packages/agent-sdk` (`AdminClient` + `AgentClient`).

## Registering an agent
```bash
# Mint an API key (returned once). Over the tailnet:
curl -X POST https://<node>.<tailnet>.ts.net/api/v1/agents \
  -H 'Content-Type: application/json' -d '{"name":"agent-01"}'
# → {"id":"…","api_key":"…  <-- store now, shown once","status":"OFFLINE", …}
```
Then the agent checks in with `X-Agent-Key: <api_key>` against `POST /api/v1/agents/checkin`.

## Agent operational protocol → API
| Step | Protocol | Endpoint |
|------|----------|----------|
| 1 | INIT (check-in) | `POST /api/v1/agents/checkin` |
| 2 | PLANNING | `POST /api/v1/sessions/{id}/plan` |
| 3 | REFINEMENT | `POST /api/v1/sessions/{id}/refine` (+ human `/feedback`) |
| 4 | EXECUTION & REPORTING | `POST /api/v1/webhooks/stage-report` |
| — | Human approval | `POST /api/v1/sessions/{id}/approve` |
| 5 | COMPLETION | `POST /api/v1/sessions/{id}/complete` |

Artifact content for the viewer: `GET /api/v1/artifacts/{gdrive_file_id}`.

## Status
- **Backend** — full protocol implemented, 11 passing tests, ruff clean, migration covers
  all 6 tables (agents, projects, sessions, commits, gdrive_references, feedback).
- **Frontend** — dashboard, project, session-manager, and artifact pages build cleanly
  (Next.js production build + `tsc` pass).

### Known follow-ups
- Agent **revocation** (`DELETE /agents/{id}`) to complement registration.
- Live updates (polling/SSE) on the dashboard; today pages fetch on load (`no-store`).
- Infinite-scroll wiring on the commit timeline (backend keyset pagination is ready).

### Done
- Full agent protocol (plan → refine → approve → report → complete), 15 passing tests.
- Live on Docker against Neon Postgres; Google Drive auth verified with the real key.
- Agent **registration** endpoint; verified a real check-in end-to-end over Tailscale.
- Tailnet exposure via `tailscale serve` (backend `:443`, dashboard `:8443`).
