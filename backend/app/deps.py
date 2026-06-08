"""Shared FastAPI dependencies."""

from functools import lru_cache

from app.services.gdrive import GDriveClient


@lru_cache
def _gdrive_singleton() -> GDriveClient:
    """Build one GDriveClient per process (the Drive service is reused across calls)."""
    return GDriveClient()


def get_gdrive() -> GDriveClient:
    """Dependency returning the GDrive client. Overridden with a fake in tests."""
    return _gdrive_singleton()
