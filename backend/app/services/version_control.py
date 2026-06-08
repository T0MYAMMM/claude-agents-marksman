"""Version-control engine: turns agent actions into immutable commit records.

A commit optionally links a GDriveReference (the uploaded Markdown) and always chains
to its parent commit, forming the Git-style timeline. This module is the single place
that writes commits, so the append-only invariant lives here.
"""

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit import Commit
from app.models.enums import CommitType
from app.models.gdrive_reference import GDriveReference


async def _latest_commit_id(db: AsyncSession, session_id: str) -> str | None:
    """Return the id of the most recent commit for a session, or None."""
    result = await db.execute(
        select(Commit.id)
        .where(Commit.session_id == session_id)
        .order_by(desc(Commit.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def record_commit(
    db: AsyncSession,
    *,
    session_id: str,
    agent_id: str,
    commit_type: CommitType,
    message: str,
    gdrive_ref: GDriveReference | None = None,
    payload: dict[str, Any] | None = None,
) -> Commit:
    """Create and persist a commit, auto-chaining it to the session's latest commit.

    The caller is responsible for committing the surrounding transaction; this function
    flushes so the new row's id is populated.
    """
    parent_id = await _latest_commit_id(db, session_id)

    if gdrive_ref is not None and gdrive_ref.id is None:
        db.add(gdrive_ref)
        await db.flush()

    commit = Commit(
        session_id=session_id,
        agent_id=agent_id,
        gdrive_ref_id=gdrive_ref.id if gdrive_ref else None,
        parent_commit_id=parent_id,
        type=commit_type,
        message=message,
        payload=payload,
    )
    db.add(commit)
    await db.flush()
    return commit
