"""Application configuration, loaded from the environment via pydantic-settings."""

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

# libpq query params that asyncpg does not understand and must be removed from the URL.
_LIBPQ_ONLY_PARAMS = {"sslmode", "channel_binding", "ssl"}


def _scheme(url: str) -> str:
    return url.split("://", 1)[0] if "://" in url else ""


def normalize_db_url(raw: str) -> str:
    """Coerce a Postgres DSN to the async driver and strip libpq-only query params.

    Accepts the connection strings cloud providers hand out verbatim (e.g. Neon's
    ``postgresql://...?sslmode=require&channel_binding=require``) and returns a URL
    asyncpg accepts. SQLite and already-async URLs pass through unchanged. SSL itself is
    re-applied via :func:`db_connect_args`.
    """
    if not raw:
        return raw
    url = raw
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    if "asyncpg" not in _scheme(url):
        return url  # sqlite or some other driver — leave as-is
    parts = urlsplit(url)
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _LIBPQ_ONLY_PARAMS
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment))


def db_connect_args(raw: str) -> dict:
    """Build asyncpg connect args, translating libpq ``sslmode`` to asyncpg ``ssl``."""
    if not _scheme(raw).startswith(("postgres", "postgresql")):
        return {}
    query = dict(parse_qsl(urlsplit(raw).query))
    mode = query.get("sslmode") or query.get("ssl")
    if mode and mode.lower() not in {"disable", "false", "0"}:
        return {"ssl": "require" if mode.lower() in {"true", "1"} else mode}
    return {}


class Settings(BaseSettings):
    """Runtime settings sourced from environment variables (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    # Database. Defaults to a local async SQLite file; override with a Postgres DSN in prod,
    # e.g. APP_DATABASE_URL=postgresql+asyncpg://user:pass@host/db
    database_url: str = "sqlite+aiosqlite:///./orchestrator.db"

    # Network trust: only requests originating from the Tailscale CGNAT range are accepted.
    # Tailscale assigns addresses in 100.64.0.0/10. Set to "" to disable (tests only).
    tailscale_cidr: str = "100.64.0.0/10"

    # Google Drive credentials. Resolution order in services/gdrive.py:
    #   1. OAuth user token (gdrive_oauth_token_path) — uploads as the user, real quota.
    #   2. Service-account file (gdrive_credentials_path).
    #   3. Service-account inline JSON (gdrive_credentials_json).
    # A service account cannot store bytes on a personal (non-Workspace) Drive, so OAuth
    # is required when artifacts must land in a personal account's Drive folder.
    gdrive_credentials_path: str = ""
    gdrive_credentials_json: str = ""
    # OAuth installed-app flow: client_secret.json from GCP, and the token produced by
    # `python -m scripts.gdrive_oauth` after the one-time browser authorization.
    gdrive_oauth_client_secret_path: str = ""
    gdrive_oauth_token_path: str = ""

    # Pagination default for commit timelines.
    default_page_size: int = 50

    # Anthropic API key for the Markdown-editing chat assistant. Empty disables the
    # chat endpoint (returns 503). Set via APP_ANTHROPIC_API_KEY.
    anthropic_api_key: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        """The database URL normalized for the async driver."""
        return normalize_db_url(self.database_url)

    @property
    def connect_args(self) -> dict:
        """Driver connect args (e.g. SSL) derived from the raw database URL."""
        return db_connect_args(self.database_url)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
