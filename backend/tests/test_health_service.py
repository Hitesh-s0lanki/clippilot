"""Unit tests for HealthService.

The service has no HTTP dependencies, so these tests exercise it directly
without building an application or issuing a request.
"""

import time
from datetime import UTC, datetime

from src.core.config import Settings
from src.services.health_service import HealthReport, HealthService


def _service(settings: Settings, started_at: float | None = None) -> HealthService:
    return HealthService(settings=settings, started_at=started_at or time.monotonic())


class TestCheck:
    def test_reports_ok_when_no_dependencies_fail(self, settings: Settings) -> None:
        report = _service(settings).check()

        assert isinstance(report, HealthReport)
        assert report.status == "ok"
        assert report.is_healthy is True

    def test_report_reflects_configured_settings(self, settings: Settings) -> None:
        report = _service(settings).check()

        assert report.service == settings.project_name
        assert report.version == settings.version
        assert report.environment == "test"

    def test_timestamp_is_timezone_aware_utc(self, settings: Settings) -> None:
        report = _service(settings).check()

        assert report.timestamp.tzinfo is not None
        assert report.timestamp.utcoffset() == datetime.now(UTC).utcoffset()

    def test_reports_degraded_when_a_dependency_is_down(self, settings: Settings) -> None:
        class DegradedService(HealthService):
            def _check_dependencies(self) -> dict[str, bool]:
                return {"database": False}

        report = DegradedService(settings=settings, started_at=time.monotonic()).check()

        assert report.status == "degraded"
        assert report.is_healthy is False
        assert report.dependencies == {"database": False}

    def test_reports_ok_when_all_dependencies_pass(self, settings: Settings) -> None:
        class HealthyService(HealthService):
            def _check_dependencies(self) -> dict[str, bool]:
                return {"database": True, "cache": True}

        report = HealthyService(settings=settings, started_at=time.monotonic()).check()

        assert report.status == "ok"
        assert report.dependencies == {"database": True, "cache": True}


class TestUptime:
    def test_uptime_is_non_negative(self, settings: Settings) -> None:
        assert _service(settings).uptime_seconds() >= 0

    def test_uptime_grows_with_elapsed_time(self, settings: Settings) -> None:
        # Start time five seconds in the past.
        service = _service(settings, started_at=time.monotonic() - 5)

        assert service.uptime_seconds() >= 5

    def test_report_is_immutable(self, settings: Settings) -> None:
        import dataclasses

        report = _service(settings).check()

        try:
            report.status = "degraded"  # type: ignore[misc]
        except dataclasses.FrozenInstanceError:
            return
        raise AssertionError("HealthReport should be immutable")
