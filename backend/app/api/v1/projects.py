"""Project CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_tailscale
from app.database import get_db
from app.deps import get_gdrive
from app.models.commit import Commit
from app.models.enums import DocCategory
from app.models.gdrive_reference import GDriveReference
from app.models.project import Project
from app.models.session import Session
from app.schemas.bookshelf import CategorySection, DocumentRead, LibraryRead
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.artifact import ensure_project_bookshelf
from app.services.gdrive import GDriveClient

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    """Create a new project workspace."""
    project = Project(
        name=body.name, description=body.description, gdrive_folder_id=body.gdrive_folder_id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[Project]:
    """List all projects (dashboard grid)."""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return list(result.scalars())


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> Project:
    """Fetch a single project by id."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)
) -> Project:
    """Partially update a project."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.post(
    "/{project_id}/bookshelf",
    response_model=ProjectRead,
    dependencies=[Depends(require_tailscale)],
)
async def provision_bookshelf(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    gdrive: GDriveClient = Depends(get_gdrive),
) -> Project:
    """Provision the project's bookshelf folders on Drive (idempotent)."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    await ensure_project_bookshelf(db, gdrive, project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}/library", response_model=LibraryRead)
async def get_library(project_id: str, db: AsyncSession = Depends(get_db)) -> LibraryRead:
    """Return the project's bookshelf documents, grouped by category."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    result = await db.execute(
        select(GDriveReference)
        .join(Commit, Commit.gdrive_ref_id == GDriveReference.id)
        .join(Session, Session.id == Commit.session_id)
        .where(Session.project_id == project_id)
        .where(GDriveReference.category.is_not(None))
        .order_by(GDriveReference.created_at.asc())
    )
    refs = list(result.scalars())

    grouped: dict[str, list[DocumentRead]] = {category.value: [] for category in DocCategory}
    for ref in refs:
        grouped[ref.category].append(DocumentRead.model_validate(ref))

    sections = [
        CategorySection(category=category.value, documents=grouped[category.value])
        for category in DocCategory
    ]
    return LibraryRead(
        project_id=project.id,
        bookshelf_folder_id=project.bookshelf_folder_id,
        sections=sections,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a project and its sessions/commits (cascade)."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    await db.delete(project)
    await db.commit()
