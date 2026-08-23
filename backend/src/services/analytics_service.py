"""Campaign analytics aggregation."""

from __future__ import annotations

from src.app.errors import ApiError
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.analytics import CampaignAnalytics, OptionBreakdown
from src.schemas.enums import OptionIntent
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
        clicks = await self._events.clicks_by_option(campaign.id)
        unique_viewers = await self._events.unique_viewers(campaign.id)
        first, last = await self._events.activity_window(campaign.id)

        metrics = mappers.build_metrics(counts, last)
        interactions = metrics.interactions

        experience = campaign.experience
        options = sorted(experience.options, key=lambda o: o.position) if experience else []

        # A row for every option, including zero-click ones: a chart with a
        # missing bar is a bug the frontend should not have to guess around.
        by_option = [
            OptionBreakdown(
                option_id=option.id,
                position=option.position,
                key=option.key,
                label=option.label,
                intent=OptionIntent(option.intent),
                clicks=clicks.get(option.id, 0),
                share=round(clicks.get(option.id, 0) / interactions, 4) if interactions else 0.0,
            )
            for option in options
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
            by_option=by_option,
            primary_metric=mappers.primary_metric_for(campaign.objective, metrics, positive_rate),
            first_activity_at=first,
            last_activity_at=last,
        )
