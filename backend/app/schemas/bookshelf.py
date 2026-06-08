"""Request/response contracts for the project bookshelf (documentation library)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocCategory


class DocumentSubmit(BaseModel):
    """A documentation artifact an agent submits to the bookshelf."""

    agent_id: str
    category: DocCategory
    file_name: str
    content: str
    commit_message: str


class DocumentRead(BaseModel):
    """A stored documentation artifact as returned by the library API."""

    model_config = ConfigDict(from_attributes=True)

    gdrive_file_id: str
    file_name: str
    category: DocCategory
    web_view_link: str | None = None
    created_at: datetime


class CategorySection(BaseModel):
    """A single bookshelf category and the documents filed under it."""

    category: str
    documents: list[DocumentRead]


class LibraryRead(BaseModel):
    """The full bookshelf for a project, grouped by category."""

    project_id: str
    bookshelf_folder_id: str | None
    sections: list[CategorySection]
