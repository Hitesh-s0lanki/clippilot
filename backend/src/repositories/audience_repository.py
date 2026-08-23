"""Database access for audiences and the people in them.

The only layer that builds SQL. The segment breakdown lives here rather than in
the service because it is an aggregation, and pulling every member into Python
to count them by city would be the one query that stops working at the size an
audience is for.
"""

from __future__ import annotations

from sqlalchemy import Case, Select, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Audience, AudienceMember, Campaign
from src.schemas.enums import AGE_GROUP_BOUNDS, AgeGroup, CampaignStatus

# How many distinct places one breakdown reports before the rest are folded
# into an "other" remainder by the caller. A list can span 200 cities; a chart
# that draws 200 bars communicates nothing.
TOP_PLACES = 8


def _age_group_case() -> Case:
    """The SQL that buckets ``age``, built from the same bounds Python uses."""
    branches = []
    for group, (low, high) in AGE_GROUP_BOUNDS.items():
        if low is None:
            condition = AudienceMember.age <= high
        elif high is None:
            condition = AudienceMember.age >= low
        else:
            condition = AudienceMember.age.between(low, high)
        branches.append((AudienceMember.age.is_not(None) & condition, group.value))

    return case(*branches, else_=AgeGroup.UNKNOWN.value)


class AudienceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- audiences ---------------------------------------------------------

    def _owned(self, owner_user_id: str) -> Select:
        """Base query scoped to one Clerk user.

        Every read goes through here, so a missing owner filter is impossible
        to introduce by forgetting a WHERE clause in a new method.
        """
        return select(Audience).where(Audience.owner_user_id == owner_user_id)

    async def get(self, audience_id: str, owner_user_id: str) -> Audience | None:
        result = await self._session.execute(
            self._owned(owner_user_id).where(Audience.id == audience_id)
        )
        return result.scalar_one_or_none()

    async def list_audiences(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Audience], int]:
        query = self._owned(owner_user_id)
        if search:
            query = query.where(Audience.name.ilike(f"%{search}%"))

        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        page = await self._session.execute(
            query.order_by(Audience.created_at.desc()).limit(limit).offset(offset)
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
            .select_from(Audience)
            .where(
                Audience.owner_user_id == owner_user_id,
                func.lower(Audience.name) == name.lower(),
            )
        )
        if exclude_id:
            query = query.where(Audience.id != exclude_id)

        return bool(await self._session.scalar(query))

    async def campaign_counts(self, audience_ids: list[str]) -> dict[str, int]:
        """How many live-able campaigns point at each audience, for a whole page."""
        if not audience_ids:
            return {}

        rows = await self._session.execute(
            select(Campaign.audience_id, func.count())
            .where(
                Campaign.audience_id.in_(audience_ids),
                Campaign.status != CampaignStatus.ARCHIVED.value,
            )
            .group_by(Campaign.audience_id)
        )

        return {str(audience_id): int(count) for audience_id, count in rows.all()}

    # --- members -----------------------------------------------------------

    def _member_query(
        self,
        audience_id: str,
        *,
        search: str | None = None,
        city: str | None = None,
        country: str | None = None,
        age_group: AgeGroup | None = None,
        gender: str | None = None,
        has_email: bool | None = None,
        has_phone: bool | None = None,
    ) -> Select:
        """One filter, shared by the page and its total so they cannot disagree."""
        query = select(AudienceMember).where(AudienceMember.audience_id == audience_id)

        if search:
            term = f"%{search}%"
            query = query.where(
                or_(
                    AudienceMember.full_name.ilike(term),
                    AudienceMember.email.ilike(term),
                    AudienceMember.phone.ilike(term),
                    AudienceMember.external_ref.ilike(term),
                )
            )
        if city:
            query = query.where(AudienceMember.city == city)
        if country:
            query = query.where(AudienceMember.country == country)
        if gender:
            query = query.where(AudienceMember.gender == gender)
        if age_group is not None:
            query = query.where(_age_group_case() == age_group.value)
        if has_email is not None:
            query = query.where(
                AudienceMember.email.is_not(None) if has_email else AudienceMember.email.is_(None)
            )
        if has_phone is not None:
            query = query.where(
                AudienceMember.phone.is_not(None) if has_phone else AudienceMember.phone.is_(None)
            )

        return query

    async def list_members(
        self, audience_id: str, *, limit: int = 25, offset: int = 0, **filters
    ) -> tuple[list[AudienceMember], int]:
        query = self._member_query(audience_id, **filters)

        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        page = await self._session.execute(
            query.order_by(AudienceMember.created_at, AudienceMember.id).limit(limit).offset(offset)
        )

        return list(page.scalars().all()), int(total or 0)

    async def all_members(self, audience_id: str) -> list[AudienceMember]:
        """Every member, oldest first. For export and for the preview switcher."""
        rows = await self._session.execute(
            select(AudienceMember)
            .where(AudienceMember.audience_id == audience_id)
            .order_by(AudienceMember.created_at, AudienceMember.id)
        )
        return list(rows.scalars().all())

    async def get_member(self, audience_id: str, member_id: str) -> AudienceMember | None:
        result = await self._session.execute(
            select(AudienceMember).where(
                AudienceMember.audience_id == audience_id,
                AudienceMember.id == member_id,
            )
        )
        return result.scalar_one_or_none()

    async def first_member(self, audience_id: str) -> AudienceMember | None:
        """Who a preview resolves against when the link names nobody."""
        result = await self._session.execute(
            select(AudienceMember)
            .where(AudienceMember.audience_id == audience_id)
            .order_by(AudienceMember.created_at, AudienceMember.id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_members(self, audience_id: str) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(AudienceMember)
            .where(AudienceMember.audience_id == audience_id)
        )
        return int(total or 0)

    async def member_emails(self, audience_id: str) -> set[str]:
        """Every email already on the list, lower-cased, for import dedup."""
        rows = await self._session.execute(
            select(func.lower(AudienceMember.email)).where(
                AudienceMember.audience_id == audience_id,
                AudienceMember.email.is_not(None),
            )
        )
        return {value for (value,) in rows.all() if value}

    # --- aggregation -------------------------------------------------------

    async def reach_counts(self, audience_id: str) -> tuple[int, int, int]:
        """(total, reachable by email, reachable by phone) in one pass."""
        row = await self._session.execute(
            select(
                func.count(),
                func.count(AudienceMember.email),
                func.count(AudienceMember.phone),
            ).where(AudienceMember.audience_id == audience_id)
        )
        total, with_email, with_phone = row.one()
        return int(total), int(with_email), int(with_phone)

    async def _grouped(self, audience_id: str, column, *, limit: int | None = None):
        query = (
            select(column, func.count())
            .where(AudienceMember.audience_id == audience_id)
            .group_by(column)
            .order_by(func.count().desc(), column)
        )
        if limit is not None:
            query = query.limit(limit)

        rows = await self._session.execute(query)
        return [(key, int(count)) for key, count in rows.all()]

    async def age_group_counts(self, audience_id: str) -> list[tuple[str, int]]:
        return await self._grouped(audience_id, _age_group_case().label("age_group"))

    async def gender_counts(self, audience_id: str) -> list[tuple[str, int]]:
        return await self._grouped(audience_id, AudienceMember.gender)

    async def city_counts(self, audience_id: str, *, limit: int = TOP_PLACES):
        return await self._grouped(audience_id, AudienceMember.city, limit=limit)

    async def country_counts(self, audience_id: str, *, limit: int = TOP_PLACES):
        return await self._grouped(audience_id, AudienceMember.country, limit=limit)

    # --- writes ------------------------------------------------------------

    def add(self, audience: Audience) -> None:
        self._session.add(audience)

    def add_member(self, member: AudienceMember) -> None:
        self._session.add(member)

    async def flush(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, audience: Audience) -> None:
        await self._session.refresh(audience)

    async def delete(self, audience: Audience) -> None:
        await self._session.delete(audience)

    async def delete_member(self, member: AudienceMember) -> None:
        await self._session.delete(member)
