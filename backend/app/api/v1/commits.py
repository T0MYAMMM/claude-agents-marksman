"""Commit timeline endpoint with keyset pagination (Commit History Timeline UI)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.pagination import decode_cursor, encode_cursor
from app.database import get_db
from app.models.commit import Commit
from app.schemas.commit import CommitPage, CommitRead

router = APIRouter(prefix="/sessions", tags=["commits"])


@router.get("/{session_id}/commits", response_model=CommitPage)
async def list_commits(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    cursor: str | None = Query(None, description="Opaque cursor from a previous page"),
    limit: int | None = Query(None, ge=1, le=200),
) -> CommitPage:
    """Return a page of a session's commits, newest first.

    Uses keyset pagination on (created_at, id) so deep histories stay fast.
    """
    page_size = limit or get_settings().default_page_size

    stmt = select(Commit).where(Commit.session_id == session_id)

    if cursor:
        try:
            ts, last_id = decode_cursor(cursor)
        except (ValueError, KeyError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Malformed cursor") from exc
        # Rows strictly older than the cursor, breaking ties by id for stability.
        stmt = stmt.where(
            or_(
                Commit.created_at < ts,
                and_(Commit.created_at == ts, Commit.id < last_id),
            )
        )

    stmt = stmt.order_by(desc(Commit.created_at), desc(Commit.id)).limit(page_size + 1)
    rows = list((await db.execute(stmt)).scalars())

    has_more = len(rows) > page_size
    page = rows[:page_size]
    next_cursor = (
        encode_cursor(page[-1].created_at, page[-1].id) if has_more and page else None
    )
    return CommitPage(
        items=[CommitRead.model_validate(c) for c in page], next_cursor=next_cursor
    )
