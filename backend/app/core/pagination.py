"""Keyset (cursor) pagination helpers for the commit timeline.

Keyset pagination keeps the timeline query O(page size) regardless of history depth,
which is what holds the dashboard under the 1-second budget. The cursor encodes the
(created_at, id) of the last seen row.
"""

import base64
import json
from datetime import datetime


def encode_cursor(created_at: datetime, commit_id: str) -> str:
    """Encode a (created_at, id) pair into an opaque base64 cursor."""
    raw = json.dumps({"ts": created_at.isoformat(), "id": commit_id})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    """Decode an opaque cursor back into (created_at, id). Raises ValueError if malformed."""
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    data = json.loads(raw)
    return datetime.fromisoformat(data["ts"]), data["id"]
