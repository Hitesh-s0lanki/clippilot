"""Campaign analytics aggregation."""

from __future__ import annotations

from src.app.errors import ApiError
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.analytics import AdBreakdown, CampaignAnalytics, OptionBreakdown
from src.schemas.enums import AdStatus, OptionIntent
from src.services import mappers


class AnalyticsService:
    def __init__(self, campaigns: CampaignRepository, events: EventRepository) -> None:
        self._campaigns = campaigns
        self._events = events

    async def for_campaign(self, campaign_id: str, owner_user_id: str) -> CampaignAnalytics:
        campaign = await self._campaigns.get(campaign_id, owner_user_id)
        if campaign is None:
            raise ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")

        counts = await self._events.counts_by_type(campaign.id)
        per_ad = await self._events.counts_by_ad(campaign.id)
        clicks = await self._events.clicks_by_option(campaign.id)
        unique_viewers = await self._events.unique_viewers(campaign.id)
        first, last = await self._events.activity_window(campaign.id)

        metrics = mappers.build_metrics(counts, last)
        interactions = metrics.interactions

        # A row for every ad and every option, including ones with no activity:
        # a chart with a missing bar is a bug the frontend should not have to
        # guess around.
        by_ad = [
            self._ad_row(ad, per_ad.get(ad.id, {}), campaign_views=metrics.views)
            for ad in campaign.ads
        ]

        by_option = [
            OptionBreakdown(
                option_id=option.id,
                ad_id=ad.id,
                position=option.position,
                key=option.key,
                label=option.label,
                intent=OptionIntent(option.intent),
                clicks=clicks.get(option.id, 0),
                share=round(clicks.get(option.id, 0) / interactions, 4) if interactions else 0.0,
            )
            for ad in campaign.ads
            for option in sorted(ad.options, key=lambda o: o.position)
        ]

        positive_clicks = sum(
            row.clicks for row in by_option if row.intent is OptionIntent.POSITIVE
        )
        positive_rate = round(positive_clicks / metrics.views, 4) if metrics.views else 0.0

        return CampaignAnalytics(
            campaign_id=campaign.id,
            objective=campaign.objective,
            views=metrics.views,
            interactions=interactions,
            interaction_rate=metrics.interaction_rate,
            unique_viewers=unique_viewers,
            by_ad=by_ad,
            by_option=by_option,
            primary_metric=mappers.primary_metric_for(campaign.objective, metrics, positive_rate),
            first_activity_at=first,
            last_activity_at=last,
        )

    @staticmethod
    def _ad_row(ad, counts: dict[str, int], *, campaign_views: int) -> AdBreakdown:
        views = counts.get("VIEW", 0)
        interactions = counts.get("RESPONSE", 0)

        return AdBreakdown(
            ad_id=ad.id,
            name=ad.name,
            status=AdStatus(ad.status),
            views=views,
            interactions=interactions,
            interaction_rate=round(interactions / views, 4) if views else 0.0,
            share_of_views=round(views / campaign_views, 4) if campaign_views else 0.0,
        )
