"""Builds the viewer-facing payloads: one campaign, and the public library.

The only responses served without a Clerk session, so each is assembled from
an explicit allow-list rather than by trimming an internal model: nothing about
the owner, budget, delivery caps, the rest of the audience or unclicked
follow-ups appears here.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.app.errors import ApiError
from src.models import Campaign
from src.models.ad import Ad
from src.models.audience import AudienceMember
from src.repositories.audience_repository import AudienceRepository
from src.repositories.campaign_repository import CampaignRepository
from src.schemas.ad import AdPublic
from src.schemas.enums import AdStatus, CampaignStatus
from src.schemas.option import OptionPublic
from src.schemas.preview import (
    CampaignPreview,
    PreviewCompliance,
    PublicCampaignCard,
    PublicCampaignPage,
)
from src.services.personalisation import (
    PersonalisationContext,
    resolve,
    unknown_variables,
)
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import (
    derive_ad_effective_status,
    derive_effective_status,
    is_ad_deliverable,
    is_viewable_by_recipient,
)


class PreviewService:
    def __init__(self, campaigns: CampaignRepository, audiences: AudienceRepository) -> None:
        self._campaigns = campaigns
        self._audiences = audiences

    async def get_public_preview(
        self,
        campaign_id: str,
        *,
        ad_id: str | None = None,
        member_id: str | None = None,
    ) -> CampaignPreview:
        """The live campaign as a member of its audience sees it.

        Two gates, because there are two levels. The campaign must be live, and
        then the ad itself must be delivering - a paused ad inside a running
        campaign is not viewable, even by its direct link.
        """
        campaign = await self._campaigns.get_public(campaign_id)
        if campaign is None:
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")

        effective = derive_effective_status(
            status=CampaignStatus(campaign.status),
            start_at=campaign.start_at,
            end_at=campaign.end_at,
            is_publishable=not collect_publish_blockers(campaign),
        )
        if not is_viewable_by_recipient(effective):
            raise ApiError(403, "CAMPAIGN_NOT_LIVE", "This campaign is not currently available.")

        ad = self._select_ad(campaign, ad_id)
        ad_effective = derive_ad_effective_status(
            status=AdStatus(ad.status),
            is_complete=ad.is_complete,
            campaign_effective=effective,
        )
        if not is_ad_deliverable(ad_effective):
            raise ApiError(403, "AD_NOT_LIVE", "This ad is not currently available.")

        return await self._render(campaign, ad, member_id=member_id)

    async def get_owner_preview(
        self,
        campaign_id: str,
        owner_user_id: str,
        *,
        ad_id: str | None = None,
        member_id: str | None = None,
    ) -> CampaignPreview:
        """The same render, for the builder's own preview.

        Scoped to the owner and allowed at any status, so a draft ad can be
        checked before it is switched on.
        """
        campaign = await self._campaigns.get(campaign_id, owner_user_id)
        if campaign is None:
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")

        return await self._render(campaign, self._select_ad(campaign, ad_id), member_id=member_id)

    async def list_public_campaigns(
        self, *, limit: int = 24, offset: int = 0
    ) -> PublicCampaignPage:
        """The ads library: every ad that is live right now.

        Rendered with nobody bound, on purpose. This listing is open to anyone,
        so ``{{customer_name}}`` resolves to the neutral fallback and no
        member's name, email or CRM reference can reach it - the personalised
        render only happens behind a campaign's own link.
        """
        ads, total = await self._campaigns.list_public_ads(
            now=datetime.now(UTC), limit=limit, offset=offset
        )

        # One card per live ad: with several creatives under one campaign, a
        # single card would silently hide all but the first. The page is
        # counted over ads too, so `total` matches what is on screen.
        return PublicCampaignPage(
            items=[self._to_card(ad.campaign, ad) for ad in ads],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _probe(self, ad):
        import traceback

        try:
            return self._to_card(ad.campaign, ad)
        except Exception:
            traceback.print_exc()
            raise

    @staticmethod
    def _to_card(campaign: Campaign, ad: Ad) -> PublicCampaignCard:
        context = PersonalisationContext(customer_name=None, campaign_name=campaign.name)

        return PublicCampaignCard(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            ad_id=ad.id,
            ad_name=ad.name,
            objective=campaign.objective,
            headline=resolve(ad.headline, context).text or None,
            preview_message=resolve(ad.personalised_message, context).text,
            poster_url=ad.poster_url,
            video_duration_seconds=ad.video_duration_seconds,
            special_category=campaign.special_category,
            option_labels=[option.label for option in sorted(ad.options, key=lambda o: o.position)],
            published_at=campaign.published_at,
        )

    @staticmethod
    def _select_ad(campaign: Campaign, ad_id: str | None) -> Ad:
        """Resolve which creative this request is about.

        Without an id the campaign picks its own primary ad, so the existing
        one-link-per-campaign flow keeps working unchanged now that a campaign
        can hold several.
        """
        if ad_id is None:
            ad = campaign.primary_ad
            if ad is None:
                raise ApiError(422, "CAMPAIGN_INCOMPLETE", "This campaign has no ads yet.")
            return ad

        for ad in campaign.ads:
            if ad.id == ad_id:
                return ad

        raise ApiError(404, "AD_NOT_FOUND", "No ad with that id on this campaign.")

    async def _render(
        self, campaign: Campaign, ad: Ad, *, member_id: str | None
    ) -> CampaignPreview:
        if not ad.video_url:
            raise ApiError(
                422,
                "CAMPAIGN_INCOMPLETE",
                "This ad has no video configured yet.",
            )

        member = await self._select_member(campaign, member_id)
        context = PersonalisationContext(
            customer_name=member.full_name if member else None,
            campaign_name=campaign.name,
            city=member.city if member else None,
            country=member.country if member else None,
        )

        headline = resolve(ad.headline, context)
        description = resolve(ad.description, context)
        message = resolve(ad.personalised_message, context)

        unresolved = sorted(
            set(headline.unresolved)
            | set(description.unresolved)
            | set(message.unresolved)
            | {
                name
                for option in ad.options
                for name in unknown_variables(option.follow_up_message)
            }
        )

        return CampaignPreview(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            customer_name=context.as_mapping()["customer_name"],
            member_id=member.id if member else None,
            ad=AdPublic(
                id=ad.id,
                video_url=ad.video_url,
                poster_url=ad.poster_url,
                captions_url=ad.captions_url,
                headline=headline.text or None,
                description=description.text or None,
                personalised_message=message.text,
                cta=ad.cta,
                options=[
                    OptionPublic(
                        id=option.id,
                        position=option.position,
                        key=option.key,
                        label=option.label,
                    )
                    for option in sorted(ad.options, key=lambda o: o.position)
                ],
            ),
            compliance=PreviewCompliance(
                special_category=campaign.special_category,
                disclaimer_text=campaign.disclaimer_text,
            ),
            unresolved_variables=unresolved,
        )

    async def _select_member(
        self, campaign: Campaign, member_id: str | None
    ) -> AudienceMember | None:
        """Who this render is personalised for.

        Fetched one row at a time rather than by loading the audience: a list
        can hold thousands of people and a render needs exactly one of them.
        With no audience selected, or a campaign opened without naming anyone,
        the copy falls back to its neutral form rather than failing.
        """
        if campaign.audience_id is None:
            return None

        if member_id is None:
            return await self._audiences.first_member(campaign.audience_id)

        member = await self._audiences.get_member(campaign.audience_id, member_id)
        if member is None:
            raise ApiError(
                404, "MEMBER_NOT_FOUND", "No member with that id in this campaign's audience."
            )

        return member
