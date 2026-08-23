"""Shared FastAPI dependency providers.

Controllers declare what they need without knowing how it is built, and tests
override any provider through ``app.dependency_overrides``.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.errors import ApiError
from src.core.config import Settings, get_settings
from src.core.security import DEV_USER_HEADER, ClerkVerifier, CurrentUser, extract_bearer_token
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.services.analytics_service import AnalyticsService
from src.services.campaign_service import CampaignService
from src.services.event_service import EventService
from src.services.health_service import HealthService
from src.services.preview_service import PreviewService
from src.services.storage_service import VideoStorage


def get_app_settings(request: Request) -> Settings:
    """Return the settings this application was built with.

    ``create_app`` stores its Settings on ``app.state``, so an app constructed
    with an explicit configuration (as tests do) is honoured everywhere instead
    of silently falling back to the process environment.
    """
    settings: Settings | None = getattr(request.app.state, "settings", None)
    return settings or get_settings()


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


# --- persistence -----------------------------------------------------------


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One database session per request, rolled back on error."""
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:  # pragma: no cover - misconfigured app
        raise ApiError(503, "DATABASE_UNAVAILABLE", "The database is not configured.")

    session: AsyncSession = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_campaign_repository(session: SessionDep) -> CampaignRepository:
    return CampaignRepository(session)


def get_event_repository(session: SessionDep) -> EventRepository:
    return EventRepository(session)


CampaignRepoDep = Annotated[CampaignRepository, Depends(get_campaign_repository)]
EventRepoDep = Annotated[EventRepository, Depends(get_event_repository)]


# --- identity --------------------------------------------------------------


def get_clerk_verifier(request: Request, settings: SettingsDep) -> ClerkVerifier:
    """One verifier per application, so the JWKS key cache is shared."""
    verifier: ClerkVerifier | None = getattr(request.app.state, "clerk_verifier", None)
    if verifier is None:
        verifier = ClerkVerifier(settings)
        request.app.state.clerk_verifier = verifier
    return verifier


async def get_current_user(
    settings: SettingsDep,
    verifier: Annotated[ClerkVerifier, Depends(get_clerk_verifier)],
    authorization: Annotated[str | None, Header()] = None,
    x_dev_user_id: Annotated[str | None, Header(alias=DEV_USER_HEADER)] = None,
) -> CurrentUser:
    """Identify the caller from the Clerk session token.

    Clerk owns sign-in and issues the token; this only verifies it. The
    X-Dev-User-Id fallback exists so the API is usable before Clerk keys are
    configured, and is refused whenever the app is not explicitly allowing it.
    """
    token = extract_bearer_token(authorization)

    if token and settings.clerk_configured:
        return await verifier.verify(token)

    if x_dev_user_id and settings.allow_dev_auth_header and not settings.is_production:
        return CurrentUser(id=x_dev_user_id.strip())

    if token and not settings.clerk_configured:
        raise ApiError(
            503,
            "AUTH_NOT_CONFIGURED",
            "Clerk is not configured on this server.",
        )

    raise ApiError(401, "NOT_AUTHENTICATED", "A Clerk session token is required.")


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


# --- services --------------------------------------------------------------


def get_health_service(request: Request, settings: SettingsDep) -> HealthService:
    """Build a HealthService bound to this application's start time."""
    started_at: float = getattr(request.app.state, "started_at", time.monotonic())
    return HealthService(settings=settings, started_at=started_at)


def get_campaign_service(campaigns: CampaignRepoDep, events: EventRepoDep) -> CampaignService:
    return CampaignService(campaigns, events)


def get_event_service(
    campaigns: CampaignRepoDep, events: EventRepoDep, settings: SettingsDep
) -> EventService:
    return EventService(campaigns, events, ip_hash_salt=settings.ip_hash_salt)


def get_preview_service(campaigns: CampaignRepoDep) -> PreviewService:
    return PreviewService(campaigns)


def get_analytics_service(campaigns: CampaignRepoDep, events: EventRepoDep) -> AnalyticsService:
    return AnalyticsService(campaigns, events)


def get_video_storage(request: Request, settings: SettingsDep) -> VideoStorage:
    """One VideoStorage per application, so the boto3 client is reused.

    Building an S3 client is expensive enough (session, credential resolution,
    endpoint discovery) that doing it per request would show up under load.
    """
    storage: VideoStorage | None = getattr(request.app.state, "video_storage", None)
    if storage is None:
        storage = VideoStorage(settings)
        request.app.state.video_storage = storage
    return storage


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
EventServiceDep = Annotated[EventService, Depends(get_event_service)]
PreviewServiceDep = Annotated[PreviewService, Depends(get_preview_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
VideoStorageDep = Annotated[VideoStorage, Depends(get_video_storage)]


def client_ip(request: Request) -> str | None:
    """Best-effort client address, honouring one proxy hop."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


ClientIpDep = Annotated[str | None, Depends(client_ip)]
