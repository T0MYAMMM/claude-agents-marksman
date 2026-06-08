# Backend — AI Agent Orchestration API

FastAPI service tracking AI-agent plans, progress, and Markdown artifacts. Metadata and
Git-style commit logs live in a relational DB; artifact bodies live in Google Drive.

## Stack
- **FastAPI** + **SQLAlchemy 2.0 (async)** + **Alembic**
- **Pydantic v2** schemas as the API contract
- **Argon2** API-key hashing; **Tailscale** CIDR source guard
- **tenacity** exponential backoff for all Google Drive calls
- SQLite (dev/test) / PostgreSQL (prod) — same models, portable types

## Layout
```
app/
├── api/v1/      # routers: agents (check-in), webhooks (stage reports), projects, commits
├── core/        # auth (Tailscale + API key), security (Argon2), pagination (keyset)
├── models/      # ORM: Agent, Project, Session, Commit, GDriveReference
├── schemas/     # Pydantic request/response contracts
├── services/    # gdrive (backoff), version_control (commit engine), session_state (FSM)
└── tests/       # pytest-asyncio: check-in, stage reports, commit chaining, FSM
```

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp ../.env.example .env          # adjust APP_* vars

alembic upgrade head             # create schema
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

## Develop
```bash
pytest -q                        # run the suite
ruff check app/                  # lint
ruff format app/                 # format
alembic revision --autogenerate -m "msg"   # new migration after model changes
```

## Implemented endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/agents/checkin` | Agent INIT: authenticate, attach to project, return context |
| POST | `/api/v1/webhooks/stage-report` | Stage progress → immutable commit |
| GET/POST/PATCH/DELETE | `/api/v1/projects` | Project CRUD |
| GET | `/api/v1/sessions/{id}/commits` | Keyset-paginated commit timeline |

## Google Drive credentials
Server-to-server uploads use a **service account** (a JSON key), not an API key.
Provide exactly one of (path wins if both are set):

```bash
APP_GDRIVE_CREDENTIALS_PATH=/secrets/gdrive-sa.json     # file (local / mounted secret)
APP_GDRIVE_CREDENTIALS_JSON={"type":"service_account",...}  # inline (secret managers)
```

Then **share the target Drive folder with the service account's `client_email` (Editor)**
and use that folder's ID as the project's `gdrive_folder_id`. Enable the Drive API in the
GCP project.

Verify the setup end to end (uploads + reads back a probe file):
```bash
python -m scripts.verify_gdrive <gdrive_folder_id>
```

## Known follow-ups
- Agent registration/admin endpoint (agents are currently seeded directly).
- Live dashboard updates (polling/SSE); pages currently fetch on load.
- Infinite-scroll wiring on the commit timeline (backend keyset pagination is ready).
