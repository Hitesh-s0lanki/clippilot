"""Application entry point.

Builds and configures the FastAPI instance. Run locally with:

    uv run uvicorn src.main:app --reload

In production the platform supplies the port:

    uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

from src.app.errors import register_exception_handlers
from src.app.router import api_router, root_router
from src.core.config import Settings, get_settings
from src.core.database import Base, build_engine, build_session_factory
from src.models import *  # noqa: F401,F403 - populates Base.metadata

logger = logging.getLogger("clippilot")

# Where the revision history lives, resolved from this file so it is found
# whatever the working directory is.
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _prepare_sqlite_schema(connection: Connection) -> None:
    """Create the schema for a fresh SQLite file, or refuse to guess.

    ``create_all`` is not a migration, and on a database Alembic already owns
    it does something worse than nothing: it adds the tables that are missing
    and silently leaves the existing ones alone. A run against a database
    stamped at an older revision therefore produces a hybrid - new tables,
    empty, beside old tables holding the data, and an existing table missing
    the column the ORM now expects. The first query then fails with
    ``no such column``, a long way from the cause.

    So: a file with no ``alembic_version`` is a fresh one and is created from
    the metadata. A file Alembic has stamped is migration-managed, and if it is
    behind we say so and stop rather than half-fixing it.
    """
    inspector = inspect(connection)

    if "alembic_version" not in inspector.get_table_names():
        Base.metadata.create_all(connection)
        return

    stamped = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
    head = ScriptDirectory(str(MIGRATIONS_DIR)).get_current_head()

    if stamped != head:
        raise RuntimeError(
            f"This SQLite database is at migration {stamped!r} but the code expects "
            f"{head!r}. Run `uv run alembic upgrade head`, or delete the file to start "
            f"from an empty one. Creating the missing tables here would leave the "
            f"database half-migrated."
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown hooks."""
    settings: Settings = app.state.settings

    # Refuse to start with a configuration that is unsafe in production.
    problems = settings.validate_runtime()
    if problems:
        for problem in problems:
            logger.error("configuration: %s", problem)
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))

    app.state.started_at = time.monotonic()

    engine = build_engine(settings)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    # Alembic owns the schema in production. Creating tables at startup is
    # limited to SQLite, which is only used for local development and tests.
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as connection:
            await connection.run_sync(_prepare_sqlite_schema)

    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory.

    Taking settings as an argument lets tests build an app with an overridden
    configuration instead of mutating the environment.
    """
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        summary="Backend for the ClipPilot interactive video campaign builder.",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Make this app's configuration reachable from dependencies.
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Operational routes at the root, business routes behind the version prefix.
    app.include_router(root_router)
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
