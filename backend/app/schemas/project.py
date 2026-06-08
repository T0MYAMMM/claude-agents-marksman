"""Request/response contracts for Project CRUD."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    """Payload to create a project."""

    name: str
    gdrive_folder_id: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Payload to update a project (all fields optional)."""

    name: str | None = None
    description: str | None = None
    gdrive_folder_id: str | None = None


class ProjectRead(BaseModel):
    """Project as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    gdrive_folder_id: str
    bookshelf_folder_id: str | None = None
    created_at: datetime
    updated_at: datetime
