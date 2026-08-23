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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.errors import register_exception_handlers
from src.app.router import api_router, root_router
from src.core.config import Settings, get_settings
from src.core.database import Base, build_engine, build_session_factory
from src.models import *  # noqa: F401,F403 - populates Base.metadata

logger = logging.getLogger("clippilot")


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
            await connection.run_sync(Base.metadata.create_all)

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
