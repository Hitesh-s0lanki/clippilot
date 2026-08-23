"""Audience business logic.

Owns the reusable lists a campaign targets: creating them, importing people
into them, filtering them and describing what they are made of. Knows nothing
about HTTP - it raises ApiError, which the error handler turns into a response.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from src.app.errors import ApiError
from src.models import Audience, AudienceMember
from src.repositories.audience_repository import AudienceRepository
from src.schemas.audience import (
    AudienceCreate,
    AudienceImportResult,
    AudienceMemberInput,
    AudienceMemberPage,
    AudiencePage,
    AudienceRead,
    AudienceSegments,
    AudienceUpdate,
    SkippedMember,
)
from src.schemas.enums import AgeGroup, Gender
from src.services import mappers
from src.services.sample_audience import SAMPLE_SEGMENTS, sample_people


class AudienceService:
    def __init__(self, audiences: AudienceRepository, *, sample_data: bool = True) -> None:
        self._audiences = audiences
        self._sample_data = sample_data

    # --- reads -------------------------------------------------------------

    async def get(self, audience_id: str, owner_user_id: str) -> AudienceRead:
        audience = await self._require(audience_id, owner_user_id)

        return mappers.audience_to_read(
            audience,
            segments=await self._segments(audience.id),
            campaign_count=await self._campaign_count(audience.id),
        )

    async def list_audiences(
        self,
        owner_user_id: str,
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> AudiencePage:
        audiences, total = await self._audiences.list_audiences(
            owner_user_id, search=search, limit=limit, offset=offset
        )

        # An account that has never had a list gets the sample ones rather than
        # an empty screen. Checked off `total` from the listing that just ran
        # instead of a count of its own, so the common path costs nothing - and
        # only when nothing is filtering it, since "no match for 'foo'" is not
        # the same as "no audiences".
        empty = total == 0 and not search and self._sample_data
        if empty and await self.provision_samples(owner_user_id):
            audiences, total = await self._audiences.list_audiences(
                owner_user_id, search=search, limit=limit, offset=offset
            )

        # One aggregate query for the whole page, not one per row.
        counts = await self._audiences.campaign_counts([a.id for a in audiences])

        return AudiencePage(
            items=[
                mappers.audience_to_list_item(a, campaign_count=counts.get(a.id, 0))
                for a in audiences
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_members(
        self,
        audience_id: str,
        owner_user_id: str,
        *,
        search: str | None = None,
        city: str | None = None,
        country: str | None = None,
        age_group: AgeGroup | None = None,
        gender: Gender | None = None,
        has_email: bool | None = None,
        has_phone: bool | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> AudienceMemberPage:
        await self._require(audience_id, owner_user_id)

        members, total = await self._audiences.list_members(
            audience_id,
            search=search,
            city=city,
            country=country,
            age_group=age_group,
            gender=gender.value if gender else None,
            has_email=has_email,
            has_phone=has_phone,
            limit=limit,
            offset=offset,
        )

        return AudienceMemberPage(
            items=[mappers.member_to_read(m) for m in members],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def segments(self, audience_id: str, owner_user_id: str) -> AudienceSegments:
        await self._require(audience_id, owner_user_id)
        return await self._segments(audience_id)

    # --- sample data ---------------------------------------------------------

    async def provision_samples(self, owner_user_id: str) -> int:
        """Give one account the sample lists. Returns how many people landed.

        Idempotent by name: a segment the owner already has is skipped, so
        running this twice does not double anybody, and an account that kept
        only one of the three gets the other two back.

        Two requests can race here - the audience screen and the campaign
        builder both list audiences, and a first visit may fire both at once.
        The unique index on (owner, lower(name)) is what actually decides it;
        the loser rolls back and reports nothing added, because by then the
        winner's rows are the truth.
        """
        added = 0

        for segment in SAMPLE_SEGMENTS:
            if await self._audiences.name_exists(owner_user_id, segment.name):
                continue

            audience = Audience(
                owner_user_id=owner_user_id,
                name=segment.name,
                description=segment.description,
                member_count=segment.size,
            )
            self._audiences.add(audience)
            await self._audiences.flush()

            for person in sample_people(segment):
                self._audiences.add_member(AudienceMember(audience_id=audience.id, **person))

            added += segment.size

        if added == 0:
            return 0

        try:
            await self._audiences.commit()
        except IntegrityError:
            # Another request provisioned first. Not an error: the account has
            # its sample lists, which is all this was for.
            await self._audiences.rollback()
            return 0

        return added

    # --- writes ------------------------------------------------------------

    async def create(self, payload: AudienceCreate, owner_user_id: str) -> AudienceRead:
        await self._guard_name(owner_user_id, payload.name)

        audience = Audience(
            owner_user_id=owner_user_id,
            name=payload.name,
            description=payload.description,
        )
        self._audiences.add(audience)
        await self._audiences.flush()

        # Duplicates inside the very first upload are skipped exactly as they
        # are on any later one, rather than failing the create.
        self._append(audience.id, payload.members, taken=set())
        await self._audiences.flush()
        audience.member_count = await self._audiences.count_members(audience.id)

        await self._commit(payload.name)

        return await self.get(audience.id, owner_user_id)

    async def update(
        self, audience_id: str, payload: AudienceUpdate, owner_user_id: str
    ) -> AudienceRead:
        audience = await self._require(audience_id, owner_user_id)
        supplied = payload.model_dump(exclude_unset=True)

        if "name" in supplied and payload.name and payload.name != audience.name:
            await self._guard_name(owner_user_id, payload.name, exclude_id=audience.id)
            audience.name = payload.name
        if "description" in supplied:
            audience.description = payload.description

        await self._commit(audience.name)

        return await self.get(audience.id, owner_user_id)

    async def delete(self, audience_id: str, owner_user_id: str) -> None:
        audience = await self._require(audience_id, owner_user_id)

        # The foreign key is SET NULL, so deleting would silently strip the
        # audience off a running campaign and leave it unpublishable with no
        # explanation. Refuse instead, and say which campaigns are in the way.
        in_use = await self._campaign_count(audience.id)
        if in_use:
            raise ApiError(
                409,
                "AUDIENCE_IN_USE",
                f"{in_use} campaign(s) still target this audience. "
                "Point them at another audience first.",
            )

        await self._audiences.delete(audience)
        await self._audiences.commit()

    async def add_members(
        self, audience_id: str, members: list[AudienceMemberInput], owner_user_id: str
    ) -> AudienceImportResult:
        """Append people to a list, skipping what cannot land rather than failing.

        A partial success is the normal outcome of a real upload. One repeated
        email in a 200-row file should cost that row, not the file - so the
        result names every skipped row instead of returning a 422 the user
        cannot act on.
        """
        audience = await self._require(audience_id, owner_user_id)

        taken = await self._audiences.member_emails(audience.id)
        skipped = self._append(audience.id, members, taken=taken)

        await self._audiences.flush()
        audience.member_count = await self._audiences.count_members(audience.id)
        await self._commit(audience.name)

        return AudienceImportResult(
            added=len(members) - len(skipped),
            skipped=skipped,
            member_count=audience.member_count,
        )

    async def remove_member(
        self, audience_id: str, member_id: str, owner_user_id: str
    ) -> AudienceRead:
        audience = await self._require(audience_id, owner_user_id)

        member = await self._audiences.get_member(audience.id, member_id)
        if member is None:
            raise ApiError(404, "MEMBER_NOT_FOUND", "No member with that id on this audience.")

        await self._audiences.delete_member(member)
        await self._audiences.flush()
        audience.member_count = await self._audiences.count_members(audience.id)
        await self._audiences.commit()

        return await self.get(audience.id, owner_user_id)

    # --- helpers -----------------------------------------------------------

    def _append(
        self, audience_id: str, members: list[AudienceMemberInput], *, taken: set[str]
    ) -> list[SkippedMember]:
        """Stage new rows, reporting the ones an email collision rules out.

        ``taken`` starts as what the audience already holds and grows as the
        batch is walked, so a file that repeats an address inside itself is
        caught by the same check that catches one already on the list.
        """
        skipped: list[SkippedMember] = []

        for index, member in enumerate(members):
            email = str(member.email).lower() if member.email else None

            if email is not None and email in taken:
                skipped.append(
                    SkippedMember(
                        index=index,
                        full_name=member.full_name,
                        reason=f"{member.email} is already on this audience",
                    )
                )
                continue

            if email is not None:
                taken.add(email)

            self._audiences.add_member(
                AudienceMember(
                    audience_id=audience_id,
                    full_name=member.full_name,
                    email=str(member.email) if member.email else None,
                    phone=member.phone,
                    age=member.age,
                    gender=member.gender.value,
                    city=member.city,
                    country=member.country,
                    external_ref=member.external_ref,
                    attributes=member.attributes,
                )
            )

        return skipped

    async def _segments(self, audience_id: str) -> AudienceSegments:
        total, with_email, with_phone = await self._audiences.reach_counts(audience_id)

        return AudienceSegments(
            total=total,
            with_email=with_email,
            with_phone=with_phone,
            age_groups=mappers.to_buckets(
                await self._audiences.age_group_counts(audience_id), total
            ),
            genders=mappers.to_buckets(await self._audiences.gender_counts(audience_id), total),
            cities=mappers.to_buckets(await self._audiences.city_counts(audience_id), total),
            countries=mappers.to_buckets(await self._audiences.country_counts(audience_id), total),
        )

    async def _campaign_count(self, audience_id: str) -> int:
        counts = await self._audiences.campaign_counts([audience_id])
        return counts.get(audience_id, 0)

    async def _require(self, audience_id: str, owner_user_id: str) -> Audience:
        """Fetch an audience the caller owns, or 404.

        Someone else's audience is reported as missing, never as forbidden, so
        ids cannot be probed for existence.
        """
        audience = await self._audiences.get(audience_id, owner_user_id)
        if audience is None:
            raise ApiError(404, "AUDIENCE_NOT_FOUND", "No audience with that id.")
        return audience

    async def _guard_name(
        self, owner_user_id: str, name: str, *, exclude_id: str | None = None
    ) -> None:
        if await self._audiences.name_exists(owner_user_id, name, exclude_id=exclude_id):
            raise ApiError(
                409,
                "AUDIENCE_NAME_TAKEN",
                f"You already have an audience called '{name}'.",
                details=[{"field": "name", "code": "DUPLICATE", "message": "Name already in use."}],
            )

    async def _commit(self, name: str) -> None:
        """Commit, turning the unique index into the same error the pre-check gives.

        The pre-check races; the index does not. Both paths have to produce one
        error shape or the frontend needs two ways to read the same failure.
        """
        try:
            await self._audiences.commit()
        except IntegrityError as exc:
            await self._audiences.rollback()
            raise ApiError(
                409,
                "AUDIENCE_NAME_TAKEN",
                f"You already have an audience called '{name}'.",
                details=[{"field": "name", "code": "DUPLICATE", "message": "Name already in use."}],
            ) from exc
