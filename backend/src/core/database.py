"""Async SQLAlchemy engine, session factory and declarative base."""

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import Settings


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def build_engine(settings: Settings) -> AsyncEngine:
    """Create an engine tuned for the configured backend.

    SQLite needs no pool sizing and rejects the pool arguments Postgres wants,
    so the keyword set differs by driver.
    """
    kwargs: dict[str, Any] = {"echo": settings.database_echo, "future": True}

    if not settings.database_url.startswith("sqlite"):
        kwargs |= {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,  # survives connections dropped by the platform
            "pool_recycle": 1800,
        }

    return create_async_engine(settings.database_url, **kwargs)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory with objects usable after commit."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def dispose_engine(engine: AsyncEngine) -> None:
    await engine.dispose()


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a session, rolling back on error and always closing.

    The request-scoped dependency in ``src.app.dependencies`` wraps this.
    """
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
