"""Ad CRUD and lifecycle.

Ads are a child of the campaign, so every method takes the campaign id and the
Clerk user and resolves both: an ad belonging to someone else's campaign is
reported as 404, never 403, so ids cannot be probed for existence.

The status rules here are the ad half of the two-level hierarchy. An ad's own
status decides whether it *wants* to deliver; whether it *does* also depends on
its campaign, which is what ``derive_ad_effective_status`` folds in.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from src.app.errors import ApiError
from src.models import Ad, Campaign
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.ad import MAX_ADS_PER_CAMPAIGN, AdInput, AdList, AdRead, AdUpdate
from src.schemas.enums import AdStatus, CampaignStatus
from src.services import mappers
from src.services.ad_builder import apply_ad_input, apply_ad_update
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import (
    derive_effective_status,
    is_ad_transition_allowed,
)


class AdService:
    def __init__(self, campaigns: CampaignRepository, events: EventRepository) -> None:
        self._campaigns = campaigns
        self._events = events

    # --- reads -------------------------------------------------------------

    async def list_ads(self, campaign_id: str, owner_user_id: str) -> AdList:
        campaign = await self._require_campaign(campaign_id, owner_user_id)
        effective = self._campaign_effective(campaign)

        return AdList(
            items=[mappers.ad_to_read(ad, campaign_effective=effective) for ad in campaign.ads],
            total=len(campaign.ads),
        )

    async def get(self, campaign_id: str, ad_id: str, owner_user_id: str) -> AdRead:
        campaign = await self._require_campaign(campaign_id, owner_user_id)
        ad = self._require_ad(campaign, ad_id)

        return mappers.ad_to_read(ad, campaign_effective=self._campaign_effective(campaign))

    # --- writes ------------------------------------------------------------

    async def create(self, campaign_id: str, payload: AdInput, owner_user_id: str) -> AdRead:
        campaign = await self._require_campaign(campaign_id, owner_user_id)
        self._guard_editable(campaign)

        if len(campaign.ads) >= MAX_ADS_PER_CAMPAIGN:
            raise ApiError(
                422,
                "AD_LIMIT_REACHED",
                f"A campaign may hold at most {MAX_ADS_PER_CAMPAIGN} ads.",
            )

        # Appended, not constructed with campaign=: doing both binds it twice
        # through back_populates and the duplicate survives the re-read.
        ad = apply_ad_input(Ad(), payload)
        campaign.ads.append(ad)
        campaign.updated_at = datetime.now(UTC)

        await self._commit(payload.name)

        return await self.get(campaign_id, ad.id, owner_user_id)

    async def update(
        self, campaign_id: str, ad_id: str, payload: AdUpdate, owner_user_id: str
    ) -> AdRead:
        campaign = await self._require_campaign(campaign_id, owner_user_id)
        self._guard_editable(campaign)
        ad = self._require_ad(campaign, ad_id)

        if ad.status == AdStatus.ARCHIVED.value:
            raise ApiError(
                409,
                "AD_INVALID_TRANSITION",
                "An archived ad cannot be edited. Duplicate it to run it again.",
            )

        apply_ad_update(ad, payload)
        ad.updated_at = datetime.now(UTC)
        campaign.updated_at = datetime.now(UTC)

        await self._commit(ad.name)

        return await self.get(campaign_id, ad_id, owner_user_id)

    async def change_status(
        self, campaign_id: str, ad_id: str, target: AdStatus, owner_user_id: str
    ) -> AdRead:
        campaign = await self._require_campaign(campaign_id, owner_user_id)
        ad = self._require_ad(campaign, ad_id)
        current = AdStatus(ad.status)

        if not is_ad_transition_allowed(current, target):
            raise ApiError(
                409,
                "AD_INVALID_TRANSITION",
                f"An ad cannot move from {current.value} to {target.value}.",
            )

        # Switching an ad on is a publish of that creative, so it must be
        # complete - the same contract the campaign enforces, one level down.
        if target is AdStatus.ACTIVE and not ad.is_complete:
            from src.services.publish_validator import collect_ad_blockers

            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "This ad is not complete enough to run.",
                details=[b.as_detail() for b in collect_ad_blockers(ad)],
            )

        ad.status = target.value
        ad.updated_at = datetime.now(UTC)
        campaign.updated_at = datetime.now(UTC)

        await self._commit(ad.name)

        return await self.get(campaign_id, ad_id, owner_user_id)

    async def delete(self, campaign_id: str, ad_id: str, owner_user_id: str) -> None:
        """Delete an ad, unless it has already been seen.

        An ad with recorded activity is archived instead of removed: its events
        carry the campaign's history, and deleting the creative they refer to
        would leave that history unexplainable.
        """
        campaign = await self._require_campaign(campaign_id, owner_user_id)
        ad = self._require_ad(campaign, ad_id)

        if await self._events.counts_for_ad(ad.id):
            raise ApiError(
                409,
                "AD_LOCKED",
                "This ad has recorded activity and can no longer be deleted. Archive it instead.",
            )

        campaign.ads.remove(ad)
        campaign.updated_at = datetime.now(UTC)
        await self._campaigns.commit()

    # --- helpers -----------------------------------------------------------

    async def _require_campaign(self, campaign_id: str, owner_user_id: str) -> Campaign:
        campaign = await self._campaigns.get(campaign_id, owner_user_id)
        if campaign is None:
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")
        return campaign

    @staticmethod
    def _require_ad(campaign: Campaign, ad_id: str) -> Ad:
        for ad in campaign.ads:
            if ad.id == ad_id:
                return ad
        raise ApiError(404, "AD_NOT_FOUND", "No ad with that id on this campaign.")

    @staticmethod
    def _guard_editable(campaign: Campaign) -> None:
        if campaign.status == CampaignStatus.ARCHIVED.value:
            raise ApiError(
                409,
                "CAMPAIGN_INVALID_TRANSITION",
                "An archived campaign cannot be edited. Duplicate it to run it again.",
            )

    @staticmethod
    def _campaign_effective(campaign: Campaign):
        return derive_effective_status(
            status=CampaignStatus(campaign.status),
            start_at=campaign.start_at,
            end_at=campaign.end_at,
            is_publishable=not collect_publish_blockers(campaign),
        )

    async def _commit(self, name: str) -> None:
        """Commit, translating the ad-name unique index into a field-level error."""
        try:
            await self._campaigns.commit()
        except IntegrityError as exc:
            await self._campaigns.rollback()
            if "uniq_ad_name_per_campaign" in str(exc.orig):
                raise ApiError(
                    409,
                    "AD_NAME_TAKEN",
                    f"This campaign already has an ad named '{name}'.",
                ) from exc
            raise ApiError(
                409, "CONSTRAINT_VIOLATION", "The change conflicts with existing data."
            ) from exc
