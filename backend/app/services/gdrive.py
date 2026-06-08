"""Google Drive client wrapper with exponential-backoff retry.

Per the non-functional requirements, every Drive call retries on transient failures
(HTTP 429 / 5xx, network drops) with exponential backoff. The Google client is built
lazily so the API can boot without credentials in dev/test.
"""

import json
import logging
from pathlib import Path
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

# Service-account scope: full Drive (used only when an SA can store bytes, e.g. a
# Workspace Shared Drive).
_SA_SCOPES = ["https://www.googleapis.com/auth/drive"]
# OAuth user scope: per-file access — the app only touches files it creates. Non-sensitive,
# so no Google app verification is required. Shared with scripts/gdrive_oauth.py.
OAUTH_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Canonical bookshelf category folders, in display order.
BOOKSHELF_CATEGORIES = [
    "overview",
    "architecture",
    "guides",
    "tutorials",
    "reference",
    "rules",
]


def _escape_drive_q(value: str) -> str:
    """Escape a value for safe interpolation into a Drive `q` query string."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


class GDriveError(RuntimeError):
    """Raised when a Drive operation ultimately fails after retries."""


def _load_oauth_credentials(token_path: str) -> Any:
    """Load OAuth user credentials, refreshing and persisting if expired."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as UserCredentials

    if not Path(token_path).exists():
        raise GDriveError(
            f"OAuth token not found at {token_path}; run `python -m scripts.gdrive_oauth`"
        )
    creds = UserCredentials.from_authorized_user_file(token_path, OAUTH_SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            Path(token_path).write_text(creds.to_json())  # persist the refreshed token
        else:
            raise GDriveError("OAuth token is invalid; re-run `python -m scripts.gdrive_oauth`")
    return creds


def _load_credentials() -> Any:
    """Resolve Drive credentials: OAuth user token first, then service account.

    OAuth is preferred because a service account has no storage quota on a personal
    Drive. Raises GDriveError if nothing is configured. Never logs key material.
    """
    from google.oauth2 import service_account  # local import: optional runtime dep

    settings = get_settings()
    if settings.gdrive_oauth_token_path:
        return _load_oauth_credentials(settings.gdrive_oauth_token_path)
    if settings.gdrive_credentials_path:
        return service_account.Credentials.from_service_account_file(
            settings.gdrive_credentials_path, scopes=_SA_SCOPES
        )
    if settings.gdrive_credentials_json:
        try:
            info = json.loads(settings.gdrive_credentials_json)
        except json.JSONDecodeError as exc:
            raise GDriveError("APP_GDRIVE_CREDENTIALS_JSON is not valid JSON") from exc
        return service_account.Credentials.from_service_account_info(info, scopes=_SA_SCOPES)
    raise GDriveError(
        "GDrive credentials not configured: set APP_GDRIVE_OAUTH_TOKEN_PATH, "
        "APP_GDRIVE_CREDENTIALS_PATH, or APP_GDRIVE_CREDENTIALS_JSON"
    )


# Retry policy shared by all Drive calls: up to 5 attempts, exponential backoff
# capped at 30s between tries. Only transient errors are retried.
_retry = retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, GDriveError)),
)


class GDriveClient:
    """Thin async-friendly wrapper around the Drive v3 API.

    The underlying google-api-python-client is synchronous; callers should run methods
    in a threadpool (e.g. anyio.to_thread) from async endpoints. Kept minimal here —
    the retry decorator is the load-bearing piece for resilience.
    """

    def __init__(self) -> None:
        self._service: Any | None = None

    def _client(self) -> Any:
        """Build the Drive service lazily from the service-account credentials."""
        if self._service is None:
            from googleapiclient.discovery import build  # local import: optional runtime dep

            creds = _load_credentials()
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    @staticmethod
    def _execute(request: Any) -> Any:
        """Run a Drive request, mapping transient HTTP errors (429/5xx) to GDriveError.

        GDriveError is in the retry set, so transient failures are retried with backoff;
        permanent errors (404/403/etc.) propagate unchanged and are not retried.
        """
        from googleapiclient.errors import HttpError

        try:
            return request.execute()
        except HttpError as exc:
            code = getattr(exc.resp, "status", None)
            if code == 429 or (code is not None and 500 <= code < 600):
                raise GDriveError(f"Transient Drive error {code}") from exc
            raise

    @_retry
    def upload_markdown(self, folder_id: str, file_name: str, content: str) -> dict[str, str]:
        """Upload a Markdown file to a Drive folder; return file metadata.

        Returns a dict with gdrive_file_id, web_view_link, and drive_revision_id.
        """
        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/markdown")
        metadata = {"name": file_name, "parents": [folder_id], "mimeType": "text/markdown"}
        request = self._client().files().create(
            body=metadata, media_body=media, fields="id, webViewLink, headRevisionId"
        )
        created = self._execute(request)
        return {
            "gdrive_file_id": created["id"],
            "web_view_link": created.get("webViewLink", ""),
            "drive_revision_id": created.get("headRevisionId", ""),
        }

    @_retry
    def ensure_folder(self, name: str, parent_id: str) -> str:
        """Return the ID of the child folder `name` under `parent_id`, creating it if absent."""
        q = (
            f"name = '{_escape_drive_q(name)}' and '{parent_id}' in parents and "
            "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        request = self._client().files().list(q=q, fields="files(id,name)")
        result = self._execute(request)
        files = result.get("files", [])
        if files:
            return files[0]["id"]
        create = self._client().files().create(
            body={
                "name": name,
                "parents": [parent_id],
                "mimeType": "application/vnd.google-apps.folder",
            },
            fields="id",
        )
        created = self._execute(create)
        return created["id"]

    def ensure_bookshelf(self, parent_id: str, project_name: str) -> dict[str, str]:
        """Ensure the project's bookshelf root + category folders exist; return their IDs.

        Returns {"root": <id>, <category>: <id>, ...} for every bookshelf category.
        Not @_retry-decorated on purpose: each ensure_folder call it makes is already
        retried individually, so wrapping the whole loop would replay completed work on a
        late transient failure (the calls are idempotent, just wasteful).
        """
        root = self.ensure_folder(project_name, parent_id)
        sections = {
            category: self.ensure_folder(category, root) for category in BOOKSHELF_CATEGORIES
        }
        return {"root": root, **sections}

    @_retry
    def update_markdown(self, file_id: str, content: str) -> dict[str, str]:
        """Overwrite a Drive file's content with new Markdown; return updated metadata.

        Returns a dict with gdrive_file_id and drive_revision_id (the new head revision).
        """
        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/markdown")
        request = self._client().files().update(
            fileId=file_id, media_body=media, fields="id, headRevisionId"
        )
        updated = self._execute(request)
        return {
            "gdrive_file_id": updated["id"],
            "drive_revision_id": updated.get("headRevisionId", ""),
        }

    @_retry
    def fetch_markdown(self, file_id: str) -> str:
        """Download and return the UTF-8 text content of a Drive file."""
        data = self._execute(self._client().files().get_media(fileId=file_id))
        return data.decode("utf-8") if isinstance(data, bytes) else str(data)

    @_retry
    def trash_file(self, file_id: str) -> bool:
        """Move a Drive file to the trash. Returns False if it was already gone (404).

        Trashing (rather than hard delete) is reversible — the file lands in the Drive
        bin. A 404 is treated as success (the file is already absent) so cleanup is
        idempotent.
        """
        from googleapiclient.errors import HttpError

        try:
            request = self._client().files().update(fileId=file_id, body={"trashed": True})
            self._execute(request)
            return True
        except HttpError as exc:
            if getattr(exc.resp, "status", None) == 404:
                return False
            raise
