"""Audience endpoints.

An audience is a top-level resource owned by the Clerk user, not a child of a
campaign - that is what makes one list reusable across campaigns. Someone
else's audience is reported as 404, never 403, so ids cannot be probed for
existence.

Membership is managed on its own routes rather than through the audience PATCH:
a list can hold thousands of people, and replacing the whole thing on every
rename would be both a footgun and a needless write.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from src.app.dependencies import AudienceServiceDep, CurrentUserDep
from src.schemas.audience import (
    AudienceCreate,
    AudienceImportResult,
    AudienceMemberPage,
    AudienceMembersInput,
    AudiencePage,
    AudienceRead,
    AudienceSegments,
    AudienceUpdate,
)
from src.schemas.enums import AgeGroup, Gender

router = APIRouter(prefix="/audiences", tags=["Audiences"])


@router.get("", response_model=AudiencePage, summary="List your audiences")
async def list_audiences(
    service: AudienceServiceDep,
    user: CurrentUserDep,
    search: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AudiencePage:
    return await service.list_audiences(user.id, search=search, limit=limit, offset=offset)


@router.post(
    "",
    response_model=AudienceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an audience",
    description=(
        "Names are unique per account, case-insensitively. Members may be "
        "supplied here or added later; a duplicate email inside the batch is "
        "skipped rather than failing the whole create."
    ),
)
async def create_audience(
    payload: AudienceCreate,
    service: AudienceServiceDep,
    user: CurrentUserDep,
    response: Response,
) -> AudienceRead:
    audience = await service.create(payload, user.id)
    response.headers["Location"] = f"/api/v1/audiences/{audience.id}"
    return audience


@router.get(
    "/{audience_id}",
    response_model=AudienceRead,
    summary="Get one audience with its segment breakdown",
)
async def get_audience(
    audience_id: str, service: AudienceServiceDep, user: CurrentUserDep
) -> AudienceRead:
    return await service.get(audience_id, user.id)


@router.patch("/{audience_id}", response_model=AudienceRead, summary="Rename an audience")
async def update_audience(
    audience_id: str,
    payload: AudienceUpdate,
    service: AudienceServiceDep,
    user: CurrentUserDep,
) -> AudienceRead:
    return await service.update(audience_id, payload, user.id)


@router.delete(
    "/{audience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an audience",
    description=(
        "Refused with 409 while any non-archived campaign still targets it, so "
        "a running campaign cannot silently lose the list it was published with."
    ),
)
async def delete_audience(
    audience_id: str, service: AudienceServiceDep, user: CurrentUserDep
) -> None:
    await service.delete(audience_id, user.id)


@router.get(
    "/{audience_id}/segments",
    response_model=AudienceSegments,
    summary="What this audience is made of",
    description=(
        "Counts by age group, gender, city and country, plus how many people "
        "are reachable by email and by phone. Names nobody."
    ),
)
async def get_segments(
    audience_id: str, service: AudienceServiceDep, user: CurrentUserDep
) -> AudienceSegments:
    return await service.segments(audience_id, user.id)


@router.get(
    "/{audience_id}/members",
    response_model=AudienceMemberPage,
    summary="List the people in an audience",
    description=(
        "Every filter combines with AND, and `total` counts what matched rather "
        "than the whole list - so a filtered page reports the size of its own "
        "segment."
    ),
)
async def list_members(
    audience_id: str,
    service: AudienceServiceDep,
    user: CurrentUserDep,
    search: Annotated[
        str | None,
        Query(max_length=120, description="Matches name, email, phone or CRM reference."),
    ] = None,
    city: Annotated[str | None, Query(max_length=80)] = None,
    country: Annotated[str | None, Query(max_length=56)] = None,
    age_group: AgeGroup | None = None,
    gender: Gender | None = None,
    has_email: Annotated[bool | None, Query(description="Only people reachable by email.")] = None,
    has_phone: Annotated[bool | None, Query(description="Only people reachable by phone.")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AudienceMemberPage:
    return await service.list_members(
        audience_id,
        user.id,
        search=search,
        city=city,
        country=country,
        age_group=age_group,
        gender=gender,
        has_email=has_email,
        has_phone=has_phone,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{audience_id}/members",
    response_model=AudienceImportResult,
    status_code=status.HTTP_201_CREATED,
    summary="Add people to an audience",
    description=(
        "One CSV upload is one call. Only `full_name` is required of each "
        "person. Rows whose email is already on the list - or repeated inside "
        "the upload - are skipped and named in the result rather than failing "
        "the batch, so a single duplicate cannot cost a 500-row file."
    ),
)
async def add_members(
    audience_id: str,
    payload: AudienceMembersInput,
    service: AudienceServiceDep,
    user: CurrentUserDep,
) -> AudienceImportResult:
    return await service.add_members(audience_id, payload.members, user.id)


@router.delete(
    "/{audience_id}/members/{member_id}",
    response_model=AudienceRead,
    summary="Remove one person from an audience",
    description="Returns the audience with its breakdown recalculated.",
)
async def remove_member(
    audience_id: str,
    member_id: str,
    service: AudienceServiceDep,
    user: CurrentUserDep,
) -> AudienceRead:
    return await service.remove_member(audience_id, member_id, user.id)
