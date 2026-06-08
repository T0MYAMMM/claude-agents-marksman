"""Artifact proxy: fetch Markdown content from Google Drive for the Artifact Viewer.

The Drive API stays server-side (credentials + Tailscale guard); the frontend reads
content through this endpoint rather than calling Drive directly.
"""

from anyio import to_thread
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_gdrive
from app.models.commit import Commit
from app.models.gdrive_reference import GDriveReference
from app.services.gdrive import GDriveClient, GDriveError

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


class ArtifactContent(BaseModel):
    """Raw Markdown content of a Drive artifact."""

    gdrive_file_id: str
    content: str


class ArtifactUpdate(BaseModel):
    """Request body for overwriting an artifact's Markdown content."""

    content: str


class ArtifactUpdated(BaseModel):
    """Metadata returned after a successful artifact update."""

    gdrive_file_id: str
    drive_revision_id: str


@router.get("/{gdrive_file_id}", response_model=ArtifactContent)
async def get_artifact(
    gdrive_file_id: str, gdrive: GDriveClient = Depends(get_gdrive)
) -> ArtifactContent:
    """Fetch a Markdown artifact's content by its Drive file ID."""
    try:
        content = await to_thread.run_sync(gdrive.fetch_markdown, gdrive_file_id)
    except GDriveError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Drive fetch failed: {exc}") from exc
    return ArtifactContent(gdrive_file_id=gdrive_file_id, content=content)


@router.patch("/{gdrive_file_id}", response_model=ArtifactUpdated)
async def update_artifact(
    gdrive_file_id: str,
    body: ArtifactUpdate,
    gdrive: GDriveClient = Depends(get_gdrive),
) -> ArtifactUpdated:
    """Overwrite a Markdown artifact's content; return the new Drive revision."""
    try:
        result = await to_thread.run_sync(
            gdrive.update_markdown, gdrive_file_id, body.content
        )
    except GDriveError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Drive update failed: {exc}") from exc
    return ArtifactUpdated(
        gdrive_file_id=result["gdrive_file_id"],
        drive_revision_id=result["drive_revision_id"],
    )


@router.delete("/{gdrive_file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    gdrive_file_id: str,
    db: AsyncSession = Depends(get_db),
    gdrive: GDriveClient = Depends(get_gdrive),
) -> None:
    """Remove an artifact from its shelf: trash the Drive file and drop its DB reference.

    Idempotent — a missing Drive file (already trashed) is fine. Commits that referenced
    the artifact are unlinked (gdrive_ref_id set NULL) so the timeline survives. Use this
    to clean up mistakenly-uploaded or duplicate documents.
    """
    ref = (
        await db.execute(
            select(GDriveReference).where(GDriveReference.gdrive_file_id == gdrive_file_id)
        )
    ).scalar_one_or_none()

    try:
        await to_thread.run_sync(gdrive.trash_file, gdrive_file_id)
    except GDriveError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Drive trash failed: {exc}") from exc

    if ref is not None:
        await db.execute(
            update(Commit).where(Commit.gdrive_ref_id == ref.id).values(gdrive_ref_id=None)
        )
        await db.delete(ref)
        await db.commit()
    # Idempotent: a missing reference (already cleaned, or a foreign file with no row) is
    # not an error — the Drive trash above is the meaningful effect either way.
