"""Database access for campaigns.

The only layer that builds SQL. Services call these methods and never import
SQLAlchemy, so swapping the persistence engine touches this directory alone.
"""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Campaign
from src.schemas.enums import CampaignStatus


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
