"""Tests for service-account credential resolution (no network)."""

import pytest

from app.config import get_settings
from app.services.gdrive import GDriveError, _load_credentials


@pytest.fixture
def _reset_creds():
    """Snapshot and restore credential settings around each test."""
    s = get_settings()
    saved = (s.gdrive_credentials_path, s.gdrive_credentials_json)
    yield s
    s.gdrive_credentials_path, s.gdrive_credentials_json = saved


def test_no_credentials_raises(_reset_creds) -> None:
    """Neither source configured -> a clear GDriveError."""
    _reset_creds.gdrive_credentials_path = ""
    _reset_creds.gdrive_credentials_json = ""
    with pytest.raises(GDriveError, match="not configured"):
        _load_credentials()


def test_malformed_inline_json_raises(_reset_creds) -> None:
    """Inline JSON that won't parse -> GDriveError, not a raw JSONDecodeError."""
    _reset_creds.gdrive_credentials_path = ""
    _reset_creds.gdrive_credentials_json = "{not valid json"
    with pytest.raises(GDriveError, match="not valid JSON"):
        _load_credentials()
