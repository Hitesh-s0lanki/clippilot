"""Database access for campaign events and their aggregation."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import CampaignEvent
from src.schemas.enums import EventType


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_session(
        self, campaign_id: str, session_id: str, event_type: EventType
    ) -> CampaignEvent | None:
        """The existing event for this session, if the dedup key already fired."""
        result = await self._session.execute(
            select(CampaignEvent).where(
                CampaignEvent.campaign_id == campaign_id,
                CampaignEvent.session_id == session_id,
                CampaignEvent.type == event_type.value,
            )
        )
        return result.scalar_one_or_none()

    async def counts_by_type(self, campaign_id: str) -> dict[str, int]:
        result = await self._session.execute(
            select(CampaignEvent.type, func.count())
            .where(CampaignEvent.campaign_id == campaign_id)
            .group_by(CampaignEvent.type)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def clicks_by_option(self, campaign_id: str) -> dict[str, int]:
        result = await self._session.execute(
            select(CampaignEvent.option_id, func.count())
            .where(
                CampaignEvent.campaign_id == campaign_id,
                CampaignEvent.type == EventType.RESPONSE.value,
                CampaignEvent.option_id.is_not(None),
            )
            .group_by(CampaignEvent.option_id)
        )
        return {str(row[0]): int(row[1]) for row in result.all()}

    async def unique_viewers(self, campaign_id: str) -> int:
        """Distinct sessions that recorded a view.

        Sessions rather than recipients: preview traffic is anonymous, so
        counting recipient_id would report 0 for the brief's core flow.
        """
        value = await self._session.scalar(
            select(func.count(func.distinct(CampaignEvent.session_id))).where(
                CampaignEvent.campaign_id == campaign_id,
                CampaignEvent.type == EventType.VIEW.value,
            )
        )
        return int(value or 0)

    async def activity_window(self, campaign_id: str) -> tuple[datetime | None, datetime | None]:
        result = await self._session.execute(
            select(
                func.min(CampaignEvent.occurred_at),
                func.max(CampaignEvent.occurred_at),
            ).where(CampaignEvent.campaign_id == campaign_id)
        )
        first, last = result.one()
        return first, last

    async def counts_for_campaigns(self, campaign_ids: list[str]) -> dict[str, dict[str, int]]:
        """Event counts for many campaigns in one query.

        The dashboard shows views and interactions per row; without this the
        listing would issue two queries per campaign.
        """
        if not campaign_ids:
            return {}

        result = await self._session.execute(
            select(CampaignEvent.campaign_id, CampaignEvent.type, func.count())
            .where(CampaignEvent.campaign_id.in_(campaign_ids))
            .group_by(CampaignEvent.campaign_id, CampaignEvent.type)
        )

        counts: dict[str, dict[str, int]] = {}
        for campaign_id, event_type, count in result.all():
            counts.setdefault(str(campaign_id), {})[str(event_type)] = int(count)
        return counts

    async def last_activity_for_campaigns(self, campaign_ids: list[str]) -> dict[str, datetime]:
        if not campaign_ids:
            return {}

        result = await self._session.execute(
            select(CampaignEvent.campaign_id, func.max(CampaignEvent.occurred_at))
            .where(CampaignEvent.campaign_id.in_(campaign_ids))
            .group_by(CampaignEvent.campaign_id)
        )
        return {str(row[0]): row[1] for row in result.all() if row[1] is not None}

    def add(self, event: CampaignEvent) -> None:
        self._session.add(event)

    async def flush(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
