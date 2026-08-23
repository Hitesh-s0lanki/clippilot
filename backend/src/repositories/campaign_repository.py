"""Database access for campaigns.

The only layer that builds SQL. Services call these methods and never import
SQLAlchemy, so swapping the persistence engine touches this directory alone.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Campaign
from src.models.ad import Ad
from src.schemas.enums import AdStatus, CampaignStatus


class CampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- reads -------------------------------------------------------------

    def _owned(self, owner_user_id: str) -> Select:
        """Base query scoped to one Clerk user.

        Every read goes through here, so a missing owner filter is impossible
        to introduce by forgetting a WHERE clause in a new method.
        """
        return select(Campaign).where(Campaign.owner_user_id == owner_user_id)

    async def get(self, campaign_id: str, owner_user_id: str) -> Campaign | None:
        result = await self._session.execute(
            self._owned(owner_user_id).where(Campaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def get_public(self, campaign_id: str) -> Campaign | None:
        """Fetch without an owner filter, for the recipient-facing preview.

        The caller is responsible for checking the campaign is live before
        exposing anything.
        """
        result = await self._session.execute(select(Campaign).where(Campaign.id == campaign_id))
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        owner_user_id: str,
        *,
        status: CampaignStatus | None = None,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Campaign], int]:
        """Return one page of campaigns plus the total matching count."""
        query = self._owned(owner_user_id)

        if status is not None:
            query = query.where(Campaign.status == status.value)
        elif not include_archived:
            # Archived campaigns are hidden unless explicitly requested.
            query = query.where(Campaign.status != CampaignStatus.ARCHIVED.value)

        if search:
            query = query.where(Campaign.name.ilike(f"%{search}%"))

        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))

        page = await self._session.execute(
            query.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
        )

        return list(page.scalars().all()), int(total or 0)

    async def list_public_ads(
        self, *, now: datetime, limit: int = 24, offset: int = 0
    ) -> tuple[list[Ad], int]:
        """One page of **ads** a stranger is allowed to see, newest campaign first.

        The library lists creatives, not campaigns - a campaign with three live
        ads contributes three cards - so the page is counted and windowed over
        ads. Counting campaigns here and returning ads would make ``total``
        disagree with what the page actually shows.

        The filter is the SQL equivalent of the two delivery gates: the
        campaign is ACTIVE and inside its schedule window, and the ad is
        switched on with a video. Ad completeness is not re-checked because an
        ad can only reach ACTIVE through a path that already enforced it -
        the status endpoint, or publish, which activates complete drafts only.
        """
        live = (
            select(Ad)
            .join(Campaign, Campaign.id == Ad.campaign_id)
            # The card is built from both the ad and its campaign, so the
            # campaign is loaded here rather than left to a lazy attribute
            # access - which would fire a query outside the async context and
            # raise, since SQLAlchemy's async layer runs in a greenlet.
            .options(selectinload(Ad.campaign))
            .where(
                Campaign.status == CampaignStatus.ACTIVE.value,
                or_(Campaign.start_at.is_(None), Campaign.start_at <= now),
                or_(Campaign.end_at.is_(None), Campaign.end_at > now),
                Ad.status == AdStatus.ACTIVE.value,
                Ad.video_url.is_not(None),
                Ad.personalised_message.is_not(None),
            )
        )

        total = await self._session.scalar(select(func.count()).select_from(live.subquery()))

        page = await self._session.execute(
            # Ordered by when the campaign went live, falling back to when it
            # was made. COALESCE rather than NULLS LAST, which SQLite and
            # Postgres spell differently.
            live.order_by(
                func.coalesce(Campaign.published_at, Campaign.created_at).desc(),
                Ad.created_at.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        return list(page.scalars().unique().all()), int(total or 0)

    async def name_exists(
        self, owner_user_id: str, name: str, *, exclude_id: str | None = None
    ) -> bool:
        """Case-insensitive name check.

        Advisory only - the unique index is the real guard. This exists to
        return a clean field-level error instead of surfacing an IntegrityError.
        """
        query = (
            select(func.count())
            .select_from(Campaign)
            .where(
                Campaign.owner_user_id == owner_user_id,
                func.lower(Campaign.name) == name.lower(),
            )
        )
        if exclude_id:
            query = query.where(Campaign.id != exclude_id)

        return bool(await self._session.scalar(query))

    # --- writes ------------------------------------------------------------

    def add(self, campaign: Campaign) -> None:
        self._session.add(campaign)

    async def flush(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, campaign: Campaign) -> None:
        await self._session.refresh(campaign)

    async def delete(self, campaign: Campaign) -> None:
        await self._session.delete(campaign)
