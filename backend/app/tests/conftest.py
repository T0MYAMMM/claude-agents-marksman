"""Shared test fixtures: in-memory DB, app override, and a registered agent."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.core.security import generate_api_key, hash_api_key
from app.database import Base, get_db
from app.deps import get_gdrive
from app.main import create_app
from app.models.agent import Agent
from app.models.project import Project


class FakeGDrive:
    """In-memory stand-in for GDriveClient — records uploads, no network."""

    def __init__(self) -> None:
        self.uploads: list[dict] = []
        self.trashed: list[str] = []
        self._counter = 0
        self.ensure_bookshelf_calls = 0

    def upload_markdown(self, folder_id: str, file_name: str, content: str) -> dict[str, str]:
        self._counter += 1
        file_id = f"drive-file-{self._counter}"
        self.uploads.append({"folder_id": folder_id, "file_name": file_name, "content": content})
        return {
            "gdrive_file_id": file_id,
            "web_view_link": f"https://drive.example/{file_id}",
            "drive_revision_id": f"rev-{self._counter}",
        }

    def fetch_markdown(self, file_id: str) -> str:
        return "# fake\n"

    def update_markdown(self, file_id: str, content: str) -> dict[str, str]:
        self.uploads.append({"file_id": file_id, "content": content, "updated": True})
        return {"gdrive_file_id": file_id, "drive_revision_id": "rev-updated"}

    def trash_file(self, file_id: str) -> bool:
        self.trashed.append(file_id)
        return True

    def ensure_folder(self, name: str, parent_id: str) -> str:
        return f"folder-{name}"

    def ensure_bookshelf(self, parent_id: str, project_name: str) -> dict[str, str]:
        self.ensure_bookshelf_calls += 1
        categories = ["overview", "architecture", "guides", "tutorials", "reference", "rules"]
        return {"root": f"root-{project_name}", **{c: f"folder-{c}" for c in categories}}


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """A fresh in-memory SQLite database per test, with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture(autouse=True)
def _disable_tailscale_guard():
    """Tests run from localhost, not the tailnet, so disable the CIDR check."""
    settings = get_settings()
    original = settings.tailscale_cidr
    settings.tailscale_cidr = ""
    yield
    settings.tailscale_cidr = original


@pytest.fixture
def fake_gdrive() -> FakeGDrive:
    """A shared FakeGDrive instance for asserting on uploads."""
    return FakeGDrive()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, fake_gdrive: FakeGDrive) -> AsyncClient:
    """An httpx client bound to the app, sharing the test's DB session and a fake Drive."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_gdrive] = lambda: fake_gdrive
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def agent_and_key(db_session: AsyncSession) -> tuple[Agent, str]:
    """A registered agent plus its plaintext API key for header auth."""
    api_key = generate_api_key()
    agent = Agent(name="test-agent", api_key_hash=hash_api_key(api_key))
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent, api_key


@pytest_asyncio.fixture
async def project(db_session: AsyncSession) -> Project:
    """A persisted project to attach sessions to."""
    proj = Project(name="Test Project", gdrive_folder_id="folder-123")
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)
    return proj
