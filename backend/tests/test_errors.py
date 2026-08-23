"""Tests for the shared error envelope.

Routes are mounted onto a throwaway app so each handler in
``src.app.errors`` is exercised against the real ASGI stack without needing
business endpoints to exist yet.
"""

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from src.app.errors import ApiError
from src.core.config import Settings
from src.main import create_app


class _Payload(BaseModel):
    name: str
    count: int


@pytest.fixture
def error_app(settings: Settings) -> FastAPI:
    app = create_app(settings)
    router = APIRouter()

    @router.get("/__test__/api-error")
    async def _api_error() -> None:
        raise ApiError(
            status_code=404,
            code="CAMPAIGN_NOT_FOUND",
            message="No campaign with that id.",
            details={"id": "abc"},
        )

    @router.get("/__test__/api-error-no-details")
    async def _api_error_no_details() -> None:
        raise ApiError(status_code=409, code="CONFLICT", message="Already published.")

    @router.get("/__test__/boom")
    async def _boom() -> None:
        raise RuntimeError("internal detail that must never reach the client")

    @router.post("/__test__/validate")
    async def _validate(payload: _Payload) -> dict[str, bool]:
        return {"ok": True}

    app.include_router(router)
    return app


class TestApiError:
    def test_uses_the_given_status_code(self, error_app: FastAPI) -> None:
        with TestClient(error_app) as client:
            assert client.get("/__test__/api-error").status_code == 404

    def test_returns_code_and_message(self, error_app: FastAPI) -> None:
        with TestClient(error_app) as client:
            body = client.get("/__test__/api-error").json()

        assert body["error"]["code"] == "CAMPAIGN_NOT_FOUND"
        assert body["error"]["message"] == "No campaign with that id."

    def test_includes_details_when_provided(self, error_app: FastAPI) -> None:
        with TestClient(error_app) as client:
            body = client.get("/__test__/api-error").json()

        assert body["error"]["details"] == {"id": "abc"}

    def test_omits_details_when_absent(self, error_app: FastAPI) -> None:
        with TestClient(error_app) as client:
            response = client.get("/__test__/api-error-no-details")

        assert response.status_code == 409
        assert "details" not in response.json()["error"]


class TestValidationError:
    def test_returns_422(self, error_app: FastAPI) -> None:
        with TestClient(error_app) as client:
            response = client.post("/__test__/validate", json={"name": "x"})

        assert response.status_code == 422

    def test_uses_the_validation_error_code_and_lists_details(self, error_app: FastAPI) -> None:
        with TestClient(error_app) as client:
            body = client.post(
                "/__test__/validate", json={"name": "x", "count": "not-a-number"}
            ).json()

        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(body["error"]["details"], list)
        assert body["error"]["details"]


class TestUnexpectedError:
    def test_returns_500_without_leaking_internals(self, error_app: FastAPI) -> None:
        # raise_server_exceptions=False lets the handler produce a response
        # instead of the exception propagating into the test.
        with TestClient(error_app, raise_server_exceptions=False) as client:
            response = client.get("/__test__/boom")

        assert response.status_code == 500

        body = response.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert body["error"]["message"] == "Something went wrong."
        assert "internal detail" not in response.text


class TestEnvelopeConsistency:
    @pytest.mark.parametrize(
        ("method", "path", "expected_status"),
        [
            ("get", "/__test__/api-error", 404),
            ("get", "/__test__/api-error-no-details", 409),
            ("get", "/definitely-not-a-route", 404),
            ("post", "/healthz", 405),
        ],
    )
    def test_every_failure_shares_one_shape(
        self, error_app: FastAPI, method: str, path: str, expected_status: int
    ) -> None:
        with TestClient(error_app) as client:
            response = getattr(client, method)(path)

        assert response.status_code == expected_status

        body = response.json()
        assert set(body) == {"error"}
        assert {"code", "message"} <= set(body["error"])
