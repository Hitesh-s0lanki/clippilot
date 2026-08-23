"""Campaign business logic.

Owns creation, editing, the publish contract and lifecycle transitions. Knows
nothing about HTTP: it raises ApiError, which the error handler turns into a
response.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from src.app.errors import ApiError
from src.models import Ad, Campaign
from src.repositories.audience_repository import AudienceRepository
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.campaign import (
    CampaignCreate,
    CampaignListItem,
    CampaignPage,
    CampaignRead,
    CampaignUpdate,
)
from src.schemas.enums import (
    DEFAULT_DISCLAIMERS,
    AdStatus,
    CampaignStatus,
    SpecialCategory,
)
from src.services import mappers
from src.services.ad_builder import apply_ad_input, guard_unique_ad_names
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import (
    UNPUBLISH_TARGET,
    is_transition_allowed,
    resolve_publish_target,
)
from src.services.validators_utm import default_utm_campaign


class CampaignService:
    def __init__(
        self,
        campaigns: CampaignRepository,
        events: EventRepository,
        audiences: AudienceRepository,
    ) -> None:
        self._campaigns = campaigns
        self._events = events
        self._audiences = audiences

    # --- reads -------------------------------------------------------------

    async def get(self, campaign_id: str, owner_user_id: str) -> CampaignRead:
        campaign = await self._require(campaign_id, owner_user_id)
        counts = await self._events.counts_by_type(campaign.id)
        _, last = await self._events.activity_window(campaign.id)

        return mappers.campaign_to_read(campaign, metrics=mappers.build_metrics(counts, last))

    async def list_campaigns(
        self,
        owner_user_id: str,
        *,
        status: CampaignStatus | None = None,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> CampaignPage:
        campaigns, total = await self._campaigns.list_campaigns(
            owner_user_id,
            status=status,
            search=search,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )

        # Two aggregate queries for the whole page, not two per row.
        ids = [c.id for c in campaigns]
        counts = await self._events.counts_for_campaigns(ids)
        last_seen = await self._events.last_activity_for_campaigns(ids)

        items: list[CampaignListItem] = [
            mappers.campaign_to_list_item(
                campaign,
                metrics=mappers.build_metrics(
                    counts.get(campaign.id, {}), last_seen.get(campaign.id)
                ),
            )
            for campaign in campaigns
        ]

        return CampaignPage(items=items, total=total, limit=limit, offset=offset)

    # --- writes ------------------------------------------------------------

    async def create(self, payload: CampaignCreate, owner_user_id: str) -> CampaignRead:
        await self._guard_name(owner_user_id, payload.name)

        campaign = Campaign(owner_user_id=owner_user_id, name=payload.name)
        self._apply_scalar_fields(campaign, payload)
        campaign.audience_id = await self._resolve_audience(payload.audience_id, owner_user_id)

        guard_unique_ad_names([ad.name for ad in payload.ads])
        for ad_input in payload.ads:
            # Appending is what binds the ad to the campaign. Passing
            # campaign= to the constructor as well would append it a second
            # time through back_populates, and the re-read after commit hits
            # the session's identity map rather than the database - so the
            # duplicate would survive into the response.
            campaign.ads.append(apply_ad_input(Ad(), ad_input))

        self._campaigns.add(campaign)
        await self._commit(owner_user_id, campaign.name)

        # Re-read rather than mapping the in-memory instance: the audience was
        # set by id and never loaded, and touching it after commit would emit a
        # lazy SELECT outside the async context.
        return await self.get(campaign.id, owner_user_id)

    async def update(
        self, campaign_id: str, payload: CampaignUpdate, owner_user_id: str
    ) -> CampaignRead:
        campaign = await self._require(campaign_id, owner_user_id)
        supplied = payload.model_dump(exclude_unset=True)

        if campaign.status == CampaignStatus.ARCHIVED.value:
            raise ApiError(
                409,
                "CAMPAIGN_INVALID_TRANSITION",
                "An archived campaign cannot be edited. Duplicate it to run it again.",
            )

        if "name" in supplied and payload.name and payload.name != campaign.name:
            await self._guard_name(owner_user_id, payload.name, exclude_id=campaign.id)
            campaign.name = payload.name

        # The objective decides what historical metrics mean, so it freezes
        # once the campaign has been published.
        if "objective" in supplied and payload.objective:
            if campaign.published_at and payload.objective.value != campaign.objective:
                raise ApiError(
                    409,
                    "CAMPAIGN_LOCKED",
                    "The objective cannot change after a campaign has been published.",
                )
            campaign.objective = payload.objective.value

        if "description" in supplied:
            campaign.description = payload.description
        if "audience_id" in supplied:
            campaign.audience_id = await self._resolve_audience(payload.audience_id, owner_user_id)

        if payload.schedule is not None:
            campaign.start_at = payload.schedule.start_at
            campaign.end_at = payload.schedule.end_at
            campaign.timezone = payload.schedule.timezone
        if payload.budget is not None:
            campaign.budget_type = payload.budget.budget_type.value
            campaign.budget_amount_minor = payload.budget.budget_amount_minor
            campaign.currency = payload.budget.currency
            campaign.spend_cap_minor = payload.budget.spend_cap_minor
        if payload.delivery is not None:
            campaign.pacing = payload.delivery.pacing.value
            campaign.send_cap_total = payload.delivery.send_cap_total
            campaign.send_cap_per_day = payload.delivery.send_cap_per_day
            campaign.frequency_cap_per_recipient = payload.delivery.frequency_cap_per_recipient
        if payload.compliance is not None:
            campaign.special_category = payload.compliance.special_category.value
            campaign.disclaimer_text = payload.compliance.disclaimer_text
        if payload.tracking is not None:
            campaign.utm_source = payload.tracking.utm_source
            campaign.utm_medium = payload.tracking.utm_medium
            campaign.utm_campaign = payload.tracking.utm_campaign
            campaign.utm_content = payload.tracking.utm_content
            campaign.external_ref = payload.tracking.external_ref

        campaign.updated_at = datetime.now(UTC)

        await self._commit(owner_user_id, campaign.name)

        return await self.get(campaign.id, owner_user_id)

    async def change_status(
        self, campaign_id: str, target: CampaignStatus, owner_user_id: str
    ) -> CampaignRead:
        campaign = await self._require(campaign_id, owner_user_id)
        current = CampaignStatus(campaign.status)

        if not is_transition_allowed(current, target):
            raise ApiError(
                409,
                "CAMPAIGN_INVALID_TRANSITION",
                f"A campaign cannot move from {current.value} to {target.value}.",
            )

        if target in {CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED}:
            blockers = collect_publish_blockers(campaign)
            if blockers:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "The campaign cannot be published.",
                    details=[b.as_detail() for b in blockers],
                )

            self._activate_ready_ads(campaign)

            resolved = resolve_publish_target(campaign.start_at)
            campaign.status = resolved.value
            if campaign.published_at is None:
                campaign.published_at = datetime.now(UTC)
            if not campaign.utm_campaign:
                campaign.utm_campaign = default_utm_campaign(campaign.name)

        elif target is UNPUBLISH_TARGET and current is not CampaignStatus.DRAFT:
            # Once a real customer has seen it, content is frozen against
            # silent rewriting.
            counts = await self._events.counts_by_type(campaign.id)
            if sum(counts.values()) > 0:
                raise ApiError(
                    409,
                    "CAMPAIGN_LOCKED",
                    "This campaign has recorded activity and can no longer be "
                    "returned to draft. Duplicate it instead.",
                )
            campaign.status = target.value

        else:
            campaign.status = target.value
            if target is CampaignStatus.ARCHIVED:
                campaign.archived_at = datetime.now(UTC)

        campaign.updated_at = datetime.now(UTC)
        await self._commit(owner_user_id, campaign.name)

        return await self.get(campaign.id, owner_user_id)

    async def delete(self, campaign_id: str, owner_user_id: str) -> None:
        campaign = await self._require(campaign_id, owner_user_id)
        await self._campaigns.delete(campaign)
        await self._campaigns.commit()

    # --- helpers -----------------------------------------------------------

    async def _require(self, campaign_id: str, owner_user_id: str) -> Campaign:
        campaign = await self._campaigns.get(campaign_id, owner_user_id)
        if campaign is None:
            # A campaign owned by someone else is reported as not found rather
            # than forbidden, so ids cannot be probed for existence.
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")
        return campaign

    async def _guard_name(
        self, owner_user_id: str, name: str, *, exclude_id: str | None = None
    ) -> None:
        if await self._campaigns.name_exists(owner_user_id, name, exclude_id=exclude_id):
            raise ApiError(
                409,
                "CAMPAIGN_NAME_TAKEN",
                "You already have a campaign with that name.",
                details=[
                    {
                        "field": "name",
                        "code": "DUPLICATE",
                        "message": "Choose a different campaign name.",
                    }
                ],
            )

    async def _commit(self, owner_user_id: str, name: str) -> None:
        """Commit, translating the unique index into a field-level error.

        The pre-check in _guard_name is advisory; this catches the race where
        two concurrent requests both pass it.
        """
        try:
            await self._campaigns.commit()
        except IntegrityError as exc:
            await self._campaigns.rollback()
            if "uniq_campaign_owner_name" in str(exc.orig):
                raise ApiError(
                    409,
                    "CAMPAIGN_NAME_TAKEN",
                    "You already have a campaign with that name.",
                ) from exc
            raise ApiError(
                409, "CONSTRAINT_VIOLATION", "The change conflicts with existing data."
            ) from exc

    def _apply_scalar_fields(self, campaign: Campaign, payload: CampaignCreate) -> None:
        campaign.description = payload.description
        campaign.objective = payload.objective.value

        campaign.start_at = payload.schedule.start_at
        campaign.end_at = payload.schedule.end_at
        campaign.timezone = payload.schedule.timezone

        campaign.budget_type = payload.budget.budget_type.value
        campaign.budget_amount_minor = payload.budget.budget_amount_minor
        campaign.currency = payload.budget.currency
        campaign.spend_cap_minor = payload.budget.spend_cap_minor

        campaign.pacing = payload.delivery.pacing.value
        campaign.send_cap_total = payload.delivery.send_cap_total
        campaign.send_cap_per_day = payload.delivery.send_cap_per_day
        campaign.frequency_cap_per_recipient = payload.delivery.frequency_cap_per_recipient

        campaign.special_category = payload.compliance.special_category.value
        campaign.disclaimer_text = payload.compliance.disclaimer_text or self._default_disclaimer(
            payload.compliance.special_category
        )

        campaign.utm_source = payload.tracking.utm_source
        campaign.utm_medium = payload.tracking.utm_medium
        campaign.utm_campaign = payload.tracking.utm_campaign or default_utm_campaign(payload.name)
        campaign.utm_content = payload.tracking.utm_content
        campaign.external_ref = payload.tracking.external_ref

    @staticmethod
    def _default_disclaimer(category: SpecialCategory) -> str | None:
        return DEFAULT_DISCLAIMERS.get(category)

    @staticmethod
    def _activate_ready_ads(campaign: Campaign) -> None:
        """Switch on every ad that is finished and has never been paused.

        Publishing the campaign is the act of going live, so an ad the user
        finished and left alone goes live with it - otherwise the common path
        (one campaign, one ad, press Publish) hands every recipient a 403.

        A **paused** ad is left paused. That is a decision the user made about
        that specific creative, and publishing the campaign is not a reason to
        undo it. Archived ads are likewise never resurrected.
        """
        for ad in campaign.ads:
            if ad.status == AdStatus.DRAFT.value and ad.is_complete:
                ad.status = AdStatus.ACTIVE.value

    async def _resolve_audience(self, audience_id: str | None, owner_user_id: str) -> str | None:
        """Check the caller owns the audience they are pointing this campaign at.

        Without this the foreign key alone would happily accept any id that
        exists, letting one account attach another account's list to its own
        campaign and read the names back through the preview. An id that is not
        theirs is reported as not found, the same as one that does not exist.
        """
        if audience_id is None:
            return None

        audience = await self._audiences.get(audience_id, owner_user_id)
        if audience is None:
            raise ApiError(
                404,
                "AUDIENCE_NOT_FOUND",
                "No audience with that id.",
                details=[
                    {
                        "field": "audience_id",
                        "code": "NOT_FOUND",
                        "message": "Choose an audience you own.",
                    }
                ],
            )

        return audience.id
