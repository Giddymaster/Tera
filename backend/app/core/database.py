"""Database engine, session factory, and declarative base.

Uses SQLAlchemy 2.x in async mode. In local development the URL points at a
SQLite file (no server needed). In production it points at PostgreSQL. The rest
of the app only ever talks to :func:`get_session`, so switching databases is a
config change, not a code change.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# SQLite needs a small tweak so a connection can be shared across async tasks;
# PostgreSQL needs none of this.
_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
)

# Enforce foreign-key constraints on SQLite (off by default there).
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_pragma(dbapi_connection, _record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session per request."""
    async with SessionLocal() as session:
        yield session


async def create_all() -> None:
    """Create tables directly from the models.

    Convenient for local development and tests. Production uses Alembic
    migrations instead (see ``backend/migrations``).
    """
    # Import models so they register on Base.metadata before create_all.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
