"""Campaign CRUD and lifecycle endpoints.

Every route is scoped to the Clerk user from the session token; a campaign
belonging to someone else is reported as 404, never 403, so ids cannot be
probed for existence.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from src.app.dependencies import (
    AnalyticsServiceDep,
    CampaignServiceDep,
    CurrentUserDep,
    PreviewServiceDep,
)
from src.schemas.analytics import CampaignAnalytics
from src.schemas.campaign import (
    CampaignCreate,
    CampaignPage,
    CampaignRead,
    CampaignUpdate,
    StatusChange,
)
from src.schemas.enums import CampaignStatus
from src.schemas.preview import CampaignPreview

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get(
    "",
    response_model=CampaignPage,
    summary="List campaigns for the dashboard",
)
async def list_campaigns(
    service: CampaignServiceDep,
    user: CurrentUserDep,
    status_filter: Annotated[
        CampaignStatus | None, Query(alias="status", description="Filter by status.")
    ] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
    include_archived: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CampaignPage:
    return await service.list_campaigns(
        user.id,
        status=status_filter,
        search=search,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a campaign",
)
async def create_campaign(
    payload: CampaignCreate,
    service: CampaignServiceDep,
    user: CurrentUserDep,
    response: Response,
) -> CampaignRead:
    campaign = await service.create(payload, user.id)
    response.headers["Location"] = f"/api/v1/campaigns/{campaign.id}"
    return campaign


@router.get("/{campaign_id}", response_model=CampaignRead, summary="Get one campaign")
async def get_campaign(
    campaign_id: str, service: CampaignServiceDep, user: CurrentUserDep
) -> CampaignRead:
    return await service.get(campaign_id, user.id)


@router.patch(
    "/{campaign_id}",
    response_model=CampaignRead,
    summary="Update a campaign",
    description="Partial update. Only the keys present in the body are applied.",
)
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    service: CampaignServiceDep,
    user: CurrentUserDep,
) -> CampaignRead:
    return await service.update(campaign_id, payload, user.id)


@router.post(
    "/{campaign_id}/status",
    response_model=CampaignRead,
    summary="Publish, pause, resume, unpublish or archive",
    description=(
        "Publishing enforces the full publish contract and returns 422 with a "
        "field-level list of blockers when it is unmet."
    ),
)
async def change_status(
    campaign_id: str,
    payload: StatusChange,
    service: CampaignServiceDep,
    user: CurrentUserDep,
) -> CampaignRead:
    return await service.change_status(campaign_id, payload.status, user.id)


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a campaign and all of its events",
)
async def delete_campaign(
    campaign_id: str, service: CampaignServiceDep, user: CurrentUserDep
) -> None:
    await service.delete(campaign_id, user.id)


@router.get(
    "/{campaign_id}/preview",
    response_model=CampaignPreview,
    summary="Preview a campaign as its owner",
    description=(
        "Renders one ad with personalisation resolved, at any status, so a "
        "draft can be checked before publishing. Without `ad_id` the campaign's "
        "primary ad is used."
    ),
)
async def preview_as_owner(
    campaign_id: str,
    service: PreviewServiceDep,
    user: CurrentUserDep,
    ad_id: Annotated[str | None, Query(description="Which ad to render.")] = None,
    member_id: Annotated[str | None, Query()] = None,
) -> CampaignPreview:
    return await service.get_owner_preview(campaign_id, user.id, ad_id=ad_id, member_id=member_id)


@router.get(
    "/{campaign_id}/analytics",
    response_model=CampaignAnalytics,
    summary="Aggregate metrics for one campaign",
)
async def get_analytics(
    campaign_id: str, service: AnalyticsServiceDep, user: CurrentUserDep
) -> CampaignAnalytics:
    return await service.for_campaign(campaign_id, user.id)
