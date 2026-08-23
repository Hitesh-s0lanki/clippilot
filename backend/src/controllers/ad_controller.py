"""Ad endpoints.

Ads are a child resource of the campaign, so every route is nested under one
and scoped to the Clerk user who owns it. An ad on someone else's campaign is
reported as 404, never 403, so ids cannot be probed for existence.

Ads are created and edited here rather than through the campaign PATCH: once a
campaign owns several creatives, replacing the whole list by index on every
campaign write is a footgun.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from src.app.dependencies import AdServiceDep, CurrentUserDep
from src.schemas.ad import AdInput, AdList, AdRead, AdStatusChange, AdUpdate

router = APIRouter(prefix="/campaigns/{campaign_id}/ads", tags=["Ads"])


@router.get("", response_model=AdList, summary="List a campaign's ads")
async def list_ads(campaign_id: str, service: AdServiceDep, user: CurrentUserDep) -> AdList:
    return await service.list_ads(campaign_id, user.id)


@router.post(
    "",
    response_model=AdRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an ad to a campaign",
    description="Ad names are unique within their campaign, case-insensitively.",
)
async def create_ad(
    campaign_id: str,
    payload: AdInput,
    service: AdServiceDep,
    user: CurrentUserDep,
    response: Response,
) -> AdRead:
    ad = await service.create(campaign_id, payload, user.id)
    response.headers["Location"] = f"/api/v1/campaigns/{campaign_id}/ads/{ad.id}"
    return ad


@router.get("/{ad_id}", response_model=AdRead, summary="Get one ad")
async def get_ad(
    campaign_id: str, ad_id: str, service: AdServiceDep, user: CurrentUserDep
) -> AdRead:
    return await service.get(campaign_id, ad_id, user.id)


@router.patch(
    "/{ad_id}",
    response_model=AdRead,
    summary="Update an ad",
    description=(
        "Partial update. Only the keys present in the body are applied; "
        "`options` replaces the whole set when supplied."
    ),
)
async def update_ad(
    campaign_id: str,
    ad_id: str,
    payload: AdUpdate,
    service: AdServiceDep,
    user: CurrentUserDep,
) -> AdRead:
    return await service.update(campaign_id, ad_id, payload, user.id)


@router.post(
    "/{ad_id}/status",
    response_model=AdRead,
    summary="Switch an ad on, pause it, or archive it",
    description=(
        "Switching an ad on enforces the ad's own completeness contract and "
        "returns 422 with a field-level list of blockers when it is unmet. An "
        "ad still only delivers while its campaign is live."
    ),
)
async def change_ad_status(
    campaign_id: str,
    ad_id: str,
    payload: AdStatusChange,
    service: AdServiceDep,
    user: CurrentUserDep,
) -> AdRead:
    return await service.change_status(campaign_id, ad_id, payload.status, user.id)


@router.delete(
    "/{ad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an ad",
    description=(
        "Refused with 409 once the ad has recorded activity - its events carry "
        "the campaign's history. Archive it instead."
    ),
)
async def delete_ad(
    campaign_id: str, ad_id: str, service: AdServiceDep, user: CurrentUserDep
) -> None:
    await service.delete(campaign_id, ad_id, user.id)
