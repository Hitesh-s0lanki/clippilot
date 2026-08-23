"""Shared pytest fixtures.

Every test builds its own application through the factory against a private
SQLite file, so tests never share state and the process environment is never
mutated.
"""

import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

import src.models  # noqa: F401 - populates Base.metadata
from src.core.config import Settings
from src.core.database import Base
from src.core.security import DEV_USER_HEADER
from src.main import create_app

OWNER = "user_test_owner"
OTHER_OWNER = "user_someone_else"

# Point this at a Postgres instance to run the suite against the deployment
# engine instead of SQLite:
#   TEST_DATABASE_URL=postgresql+asyncpg://user@host:5432/db uv run pytest
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "").strip()
USING_POSTGRES = TEST_DATABASE_URL.startswith("postgresql")


async def _reset_postgres_schema(url: str) -> None:
    """Drop and recreate every table, so each test starts from empty."""
    # NullPool: a pooled connection would outlive this loop and be reused
    # from another, which asyncpg rejects.
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
def _clean_database() -> Iterator[None]:
    """Isolate tests sharing one Postgres database.

    SQLite gets a fresh file per test via tmp_path, so this is a no-op there.
    """
    if USING_POSTGRES:
        asyncio.run(_reset_postgres_schema(TEST_DATABASE_URL))
    yield


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Deterministic settings for tests, independent of any local .env."""
    return Settings(
        project_name="ClipPilot API",
        version="0.1.0",
        environment="test",
        # Mirrors production. With debug=True Starlette's ServerErrorMiddleware
        # renders a traceback instead of delegating to our Exception handler,
        # so the "internals must not leak" guarantee would go untested.
        debug=False,
        api_prefix="/api/v1",
        cors_origins="http://localhost:5173",
        database_url=TEST_DATABASE_URL or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        allow_dev_auth_header=True,
        ip_hash_salt="test-salt",
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    """A fresh application instance configured for tests."""
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Unauthenticated client, used as a context manager so lifespan runs."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def owner_client(client: TestClient) -> TestClient:
    """Client carrying an identity, standing in for a Clerk session token."""
    client.headers[DEV_USER_HEADER] = OWNER
    return client


@pytest.fixture
def api(settings: Settings) -> str:
    return settings.api_prefix


@pytest.fixture
def draft_payload() -> dict:
    """The brief's illustrative campaign, as a complete publishable payload."""
    return {
        "name": "Investment Opportunity",
        "objective": "LEAD_CAPTURE",
        "compliance": {
            "special_category": "FINANCIAL_PRODUCTS_SERVICES",
            "disclaimer_text": "Investments are subject to market risk.",
        },
        "experience": {
            "video_url": "https://cdn.example.com/investment.mp4",
            "personalised_message": (
                "Hi {{customer_name}}, we have identified an investment opportunity for you."
            ),
            "options": [
                {
                    "position": 1,
                    "label": "Tell me more",
                    "intent": "POSITIVE",
                    "follow_up_type": "MESSAGE",
                    "follow_up_message": "Great, {{customer_name}} - an advisor will call.",
                },
                {
                    "position": 2,
                    "label": "Not interested",
                    "intent": "NEGATIVE",
                    "follow_up_type": "MESSAGE",
                    "follow_up_message": "No problem, we won't follow up.",
                },
            ],
        },
        "recipients": [{"customer_name": "Rahul"}],
    }


@pytest.fixture
def published_campaign(owner_client: TestClient, api: str, draft_payload: dict) -> dict:
    """A campaign created and published, ready for recipient traffic."""
    created = owner_client.post(f"{api}/campaigns", json=draft_payload)
    assert created.status_code == 201, created.text

    campaign_id = created.json()["id"]
    published = owner_client.post(
        f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
    )
    assert published.status_code == 200, published.text

    return published.json()
