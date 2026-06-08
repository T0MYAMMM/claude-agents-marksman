"""GDriveReference model: a pointer to a Markdown artifact stored in Google Drive."""

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import DocCategory
from app.models.mixins import TimestampMixin, UUIDPrimaryKey


class GDriveReference(Base, UUIDPrimaryKey, TimestampMixin):
    """Metadata pointing at a file in Drive. The file body is never stored in the DB."""

    __tablename__ = "gdrive_references"

    gdrive_file_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="text/markdown", nullable=False)
    web_view_link: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Drive's native revision ID for this specific version of the file.
    drive_revision_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Bookshelf category, set only for documentation artifacts (null otherwise).
    category: Mapped[str | None] = mapped_column(
        Enum(DocCategory, native_enum=False, length=16), nullable=True
    )
