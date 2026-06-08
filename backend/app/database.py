"""Async SQLAlchemy engine, session factory, and the declarative base."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_settings = get_settings()
engine = create_async_engine(
    _settings.sqlalchemy_url,
    connect_args=_settings.connect_args,
    echo=False,
    future=True,
    # Neon (serverless Postgres) closes idle connections, leaving stale ones in the pool
    # that raise asyncpg "connection is closed" InterfaceError on reuse. pre_ping validates
    # each connection before use (recycling dead ones); recycle caps connection age below
    # Neon's idle timeout. Fixes the intermittent 500s on writes after idle periods.
    pool_pre_ping=True,
    pool_recycle=280,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session and ensures cleanup."""
    async with SessionLocal() as session:
        yield session
