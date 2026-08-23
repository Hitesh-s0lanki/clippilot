"""Response schemas for the health endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

HealthStatus = Literal["ok", "degraded"]


class HealthResponse(BaseModel):
    """Payload returned by ``GET /healthz``."""

    status: HealthStatus = Field(
        ...,
        description="'ok' when every dependency is reachable, otherwise 'degraded'.",
        examples=["ok"],
    )
    service: str = Field(..., description="Human-readable service name.")
    version: str = Field(..., description="Deployed application version.")
    environment: str = Field(..., description="Environment the service is running in.")
    uptime_seconds: float = Field(
        ...,
        ge=0,
        description="Seconds elapsed since the process started serving requests.",
    )
    timestamp: datetime = Field(..., description="Server time when the check ran (UTC).")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "service": "ClipPilot API",
                    "version": "0.1.0",
                    "environment": "development",
                    "uptime_seconds": 12.48,
                    "timestamp": "2026-08-21T11:44:03.120Z",
                }
            ]
        }
    }
