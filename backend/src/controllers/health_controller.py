"""HTTP layer for health checks.

Controllers translate between HTTP and the service layer. They contain no
business rules: this one calls HealthService and maps the resulting
HealthReport onto the response schema.
"""

from fastapi import APIRouter, Response, status

from src.app.dependencies import HealthServiceDep
from src.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness and readiness probe",
    description=(
        "Returns the service status, version and uptime. Responds 200 when "
        "every dependency is reachable and 503 when any check fails, so "
        "platform health checks can react automatically."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "One or more dependencies are unreachable.",
            "model": HealthResponse,
        }
    },
)
async def healthz(service: HealthServiceDep, response: Response) -> HealthResponse:
    """Report whether this instance is able to serve traffic."""
    report = service.check()

    if not report.is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=report.status,
        service=report.service,
        version=report.version,
        environment=report.environment,
        uptime_seconds=report.uptime_seconds,
        timestamp=report.timestamp,
    )
