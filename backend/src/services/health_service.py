"""Business logic for service health reporting.

This module is deliberately free of any HTTP or FastAPI imports: it can be
called from a request handler, a CLI task or a background worker without
change. The controller layer is responsible for turning a ``HealthReport``
into an HTTP response.
"""

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.core.config import Settings


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Framework-agnostic result of a health check."""

    status: str
    service: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: datetime
    dependencies: dict[str, bool] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == "ok"


class HealthService:
    """Reports whether the service and its dependencies are usable.

    ``started_at`` is a monotonic timestamp captured when the application
    boots, so uptime is unaffected by wall-clock adjustments.
    """

    def __init__(self, settings: Settings, started_at: float) -> None:
        self._settings = settings
        self._started_at = started_at

    def check(self) -> HealthReport:
        """Run every dependency check and summarise the result."""
        dependencies = self._check_dependencies()
        status = "ok" if all(dependencies.values()) else "degraded"

        return HealthReport(
            status=status,
            service=self._settings.project_name,
            version=self._settings.version,
            environment=self._settings.environment,
            uptime_seconds=self.uptime_seconds(),
            timestamp=datetime.now(UTC),
            dependencies=dependencies,
        )

    def uptime_seconds(self) -> float:
        """Seconds elapsed since the application started, to 3 decimal places."""
        return round(time.monotonic() - self._started_at, 3)

    def _check_dependencies(self) -> dict[str, bool]:
        """Probe downstream dependencies.

        Currently there are none: the service is stateless until the database
        layer lands. When Postgres is wired up, add its reachability probe
        here (e.g. ``{"database": await self._db.ping()}``) and ``check()``
        will start reporting "degraded" automatically.
        """
        return {}
