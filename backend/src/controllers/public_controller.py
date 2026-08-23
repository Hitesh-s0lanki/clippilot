"""Recipient-facing endpoints.

The only unauthenticated routes in the API: a customer opening a video journey
has no Clerk session. They are therefore restricted to campaigns whose
effective status is ACTIVE, and they expose an explicit allow-list of fields.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from src.app.dependencies import ClientIpDep, EventServiceDep, PreviewServiceDep
from src.schemas.event import EventRead, ResponseEventCreate, ResponseResult, ViewEventCreate
from src.schemas.preview import CampaignPreview

router = APIRouter(prefix="/public/campaigns", tags=["Recipient preview"])


@router.get(
    "/{campaign_id}",
    response_model=CampaignPreview,
    summary="Open a live campaign as a recipient",
    responses={403: {"description": "The campaign is not currently live."}},
)
async def open_campaign(
    campaign_id: str,
    service: PreviewServiceDep,
    recipient_id: Annotated[str | None, Query()] = None,
) -> CampaignPreview:
    return await service.get_public_preview(campaign_id, recipient_id=recipient_id)


@router.post(
    "/{campaign_id}/views",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a video view",
    description=(
        "Idempotent per session_id. A repeat call returns 200 with the original "
        "event and deduplicated=true rather than an error."
    ),
)
async def record_view(
    campaign_id: str,
    payload: ViewEventCreate,
    service: EventServiceDep,
    response: Response,
    client_ip: ClientIpDep,
    user_agent: Annotated[str | None, Header()] = None,
) -> EventRead:
    event = await service.record_view(
        campaign_id,
        payload.session_id,
        recipient_id=payload.recipient_id,
        user_agent=user_agent,
        client_ip=client_ip,
    )
    if event.deduplicated:
        response.status_code = status.HTTP_200_OK
    return event


@router.post(
    "/{campaign_id}/responses",
    response_model=ResponseResult,
    status_code=status.HTTP_201_CREATED,
    summary="Record a response and return the follow-up",
    description=(
        "Idempotent per session_id. A repeat call returns the follow-up for the "
        "option originally chosen, so a double-click cannot switch the outcome."
    ),
)
async def record_response(
    campaign_id: str,
    payload: ResponseEventCreate,
    service: EventServiceDep,
    response: Response,
    client_ip: ClientIpDep,
    user_agent: Annotated[str | None, Header()] = None,
) -> ResponseResult:
    result = await service.record_response(
        campaign_id,
        payload.session_id,
        payload.option_id,
        recipient_id=payload.recipient_id,
        user_agent=user_agent,
        client_ip=client_ip,
    )
    if result.event.deduplicated:
        response.status_code = status.HTTP_200_OK
    return result
