"""Upload-and-commit flow shared by plan, refinement, and completion endpoints.

Uploads Markdown to the project's Drive folder (off the event loop), persists a
GDriveReference, then records the commit via the version-control engine.
"""

from anyio import to_thread
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit import Commit
from app.models.enums import CommitType, DocCategory
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project
from app.services.gdrive import GDriveClient
from app.services.version_control import record_commit


async def upload_and_commit(
    db: AsyncSession,
    gdrive: GDriveClient,
    *,
    session_id: str,
    agent_id: str,
    gdrive_folder_id: str,
    file_name: str,
    content: str,
    commit_type: CommitType,
    message: str,
    category: DocCategory | None = None,
) -> tuple[Commit, GDriveReference]:
    """Upload Markdown to Drive and record a commit linking the resulting file.

    The Drive client is synchronous, so the call runs in a worker thread to avoid
    blocking the event loop. Returns the new commit and its Drive reference.
    """
    meta = await to_thread.run_sync(gdrive.upload_markdown, gdrive_folder_id, file_name, content)

    ref = GDriveReference(
        gdrive_file_id=meta["gdrive_file_id"],
        file_name=file_name,
        web_view_link=meta.get("web_view_link") or None,
        drive_revision_id=meta.get("drive_revision_id") or None,
        category=category,
    )
    commit = await record_commit(
        db,
        session_id=session_id,
        agent_id=agent_id,
        commit_type=commit_type,
        message=message,
        gdrive_ref=ref,
    )
    return commit, ref


async def ensure_project_bookshelf(
    db: AsyncSession, gdrive: GDriveClient, project: Project
) -> dict[str, str]:
    """Ensure the project's bookshelf folders exist; return the category->folder map.

    Idempotent: if the project already has provisioned sections, returns them without
    any Drive calls. Otherwise provisions the folders on Drive (off the event loop),
    records the resulting IDs on the project, and stages it for the caller to commit.
    """
    if project.bookshelf_sections is not None:
        return project.bookshelf_sections

    result = await to_thread.run_sync(
        gdrive.ensure_bookshelf, project.gdrive_folder_id, project.name
    )
    project.bookshelf_folder_id = result["root"]
    project.bookshelf_sections = {k: v for k, v in result.items() if k != "root"}
    db.add(project)
    return project.bookshelf_sections
