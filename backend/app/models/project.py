"""Project model: a workspace grouping related agent sessions."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey, _utcnow


class Project(Base, UUIDPrimaryKey, TimestampMixin):
    """A development workspace whose artifacts live under one Google Drive folder."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Root Drive folder ID where this project's Markdown artifacts are stored.
    gdrive_folder_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # Root Drive folder ID of this project's bookshelf (documentation library).
    bookshelf_folder_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Map of category name -> Drive folder ID for each bookshelf section.
    bookshelf_sections: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    sessions: Mapped[list["Session"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
