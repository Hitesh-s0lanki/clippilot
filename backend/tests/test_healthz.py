"""Integration tests for GET /healthz.

These go through the real ASGI stack: routing, dependency injection,
serialisation and the response model.
"""

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.dependencies import get_health_service
from src.core.config import Settings
from src.services.health_service import HealthService

EXPECTED_FIELDS = {
    "status",
    "service",
    "version",
    "environment",
    "uptime_seconds",
    "timestamp",
}


class TestHealthzSuccess:
    def test_returns_200(self, client: TestClient) -> None:
        assert client.get("/healthz").status_code == 200

    def test_returns_json_content_type(self, client: TestClient) -> None:
        response = client.get("/healthz")

        assert response.headers["content-type"].startswith("application/json")

    def test_payload_contains_exactly_the_documented_fields(self, client: TestClient) -> None:
        body = client.get("/healthz").json()

        assert set(body) == EXPECTED_FIELDS

    def test_reports_ok_status(self, client: TestClient) -> None:
        assert client.get("/healthz").json()["status"] == "ok"

    def test_payload_reflects_application_settings(
        self, client: TestClient, settings: Settings
    ) -> None:
        body = client.get("/healthz").json()

        assert body["service"] == settings.project_name
        assert body["version"] == settings.version
        assert body["environment"] == "test"

    def test_uptime_is_a_non_negative_number(self, client: TestClient) -> None:
        uptime = client.get("/healthz").json()["uptime_seconds"]

        assert isinstance(uptime, int | float)
        assert uptime >= 0

    def test_timestamp_is_iso_8601(self, client: TestClient) -> None:
        from datetime import datetime

        raw = client.get("/healthz").json()["timestamp"]
        parsed = datetime.fromisoformat(raw)

        assert parsed.tzinfo is not None

    def test_is_repeatable(self, client: TestClient) -> None:
        first = client.get("/healthz")
        second = client.get("/healthz")

        assert first.status_code == second.status_code == 200
        assert second.json()["uptime_seconds"] >= first.json()["uptime_seconds"]


class TestHealthzDegraded:
    def test_returns_503_when_a_dependency_is_down(self, app: FastAPI, settings: Settings) -> None:
        class DegradedService(HealthService):
            def _check_dependencies(self) -> dict[str, bool]:
                return {"database": False}

        app.dependency_overrides[get_health_service] = lambda: DegradedService(
            settings=settings, started_at=time.monotonic()
        )

        with TestClient(app) as client:
            response = client.get("/healthz")

        assert response.status_code == 503
        assert response.json()["status"] == "degraded"

        app.dependency_overrides.clear()


class TestHealthzRouting:
    def test_is_mounted_at_the_root_not_behind_the_api_prefix(
        self, client: TestClient, settings: Settings
    ) -> None:
        # Platform probes hit /healthz without knowing the version prefix.
        assert client.get(f"{settings.api_prefix}/healthz").status_code == 404

    def test_rejects_unsupported_methods(self, client: TestClient) -> None:
        assert client.post("/healthz").status_code == 405

    def test_is_documented_in_the_openapi_schema(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()

        assert "/healthz" in schema["paths"]
        assert "200" in schema["paths"]["/healthz"]["get"]["responses"]
        assert "503" in schema["paths"]["/healthz"]["get"]["responses"]


class TestErrorEnvelope:
    def test_unknown_route_returns_the_standard_error_shape(self, client: TestClient) -> None:
        body = client.get("/does-not-exist").json()

        assert set(body) == {"error"}
        assert set(body["error"]) == {"code", "message"}
