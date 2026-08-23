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


@pytest.fixture(autouse=True, scope="session")
def _ignore_dotenv() -> Iterator[None]:
    """Keep the developer's ``.env`` out of every test in the suite.

    ``Settings`` reads ``backend/.env`` by default, so any field a test does
    not name explicitly comes from whatever that machine happens to have
    configured. That is not hypothetical: real S3 values in ``.env`` silently
    changed the bucket and the presign lifetime a storage test asserted on, and
    a model key silently armed the agents - which turned the "not configured"
    test into a failure and let the suite make billable API calls.

    Patching it off once, for the whole session, is the version of this fix
    that cannot rot: a new ``Settings(...)`` in a new test is covered without
    anyone remembering to opt out.
    """
    original = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    try:
        yield
    finally:
        Settings.model_config["env_file"] = original


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
    """Deterministic settings for tests, independent of any local .env.

    ``_env_file=None`` is what makes that sentence true. Without it pydantic
    still reads ``backend/.env``, so every field this fixture does not name
    explicitly comes from whatever the developer happens to have configured -
    and a machine with a model key would silently arm the agents, turn the
    "not configured" test into a failure, and let a test suite make billable
    API calls. Naming the sensitive fields one by one would work until someone
    adds the next one; switching the file off cannot rot.
    """
    return Settings(
        _env_file=None,
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
        # Off by default so a test that lists an empty account gets an empty
        # account. The provisioning itself is covered by tests that turn it
        # back on deliberately.
        sample_audiences=False,
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
def sample_data_client(settings: Settings) -> Iterator[TestClient]:
    """An owner client whose app hands new accounts the sample audiences.

    Its own application rather than an override on the shared one: the setting
    is read when the service is built, and a test that wants the demo
    behaviour wants it for the whole request, lifespan included.
    """
    app = create_app(settings.model_copy(update={"sample_audiences": True}))
    with TestClient(app) as test_client:
        test_client.headers[DEV_USER_HEADER] = OWNER
        yield test_client


@pytest.fixture
def api(settings: Settings) -> str:
    return settings.api_prefix


@pytest.fixture
def draft_payload(audience: dict) -> dict:
    """The brief's illustrative campaign, as a complete publishable payload.

    It targets the one-person audience rather than carrying a name of its own -
    the brief's single customer is a list of one.
    """
    return {
        "audience_id": audience["id"],
        "name": "Investment Opportunity",
        "objective": "LEAD_CAPTURE",
        "compliance": {
            "special_category": "FINANCIAL_PRODUCTS_SERVICES",
            "disclaimer_text": "Investments are subject to market risk.",
        },
        "ads": [
            {
                "name": "Investment Opportunity - advisor call",
                "video_url": "https://cdn.example.com/investment.mp4",
                "headline": "An opportunity picked for you",
                "description": "Reviewed by an advisor, matched to your risk profile.",
                "cta": "LEARN_MORE",
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
            }
        ],
    }


@pytest.fixture
def audience_payload() -> dict:
    """The brief's single customer, as the one-person audience it now is."""
    return {
        "name": "Investment Opportunity - Q3 HNI",
        "description": "The list the illustrative campaign targets.",
        "members": [
            {
                "full_name": "Rahul",
                "email": "rahul@example.com",
                "age": 41,
                "gender": "MALE",
                "city": "Mumbai",
                "country": "India",
                "external_ref": "CRM-88213",
            }
        ],
    }


@pytest.fixture
def audience(owner_client: TestClient, api: str, audience_payload: dict) -> dict:
    """One audience of one person, owned by OWNER."""
    created = owner_client.post(f"{api}/audiences", json=audience_payload)
    assert created.status_code == 201, created.text
    return created.json()


@pytest.fixture
def published_campaign(owner_client: TestClient, api: str, draft_payload: dict) -> dict:
    """A campaign created and published, ready for viewer traffic."""
    created = owner_client.post(f"{api}/campaigns", json=draft_payload)
    assert created.status_code == 201, created.text

    campaign_id = created.json()["id"]
    published = owner_client.post(
        f"{api}/campaigns/{campaign_id}/status", json={"status": "ACTIVE"}
    )
    assert published.status_code == 200, published.text

    return published.json()
