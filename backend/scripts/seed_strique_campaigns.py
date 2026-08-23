"""Seed the sample campaigns - seven, over the nine videos on strique.io.

    uv run python -m scripts.seed_strique_campaigns --owner user_dev

Gives one account a dashboard worth looking at: a spread of objectives, every
lifecycle state (live, scheduled, paused, finished, half-built), single- and
multi-ad campaigns, and roughly a thousand recorded sessions so the analytics
screen has real numbers in it. The catalogue itself is
``src/services/sample_campaign.py``.

Unlike the sample audiences, campaigns are **not** provisioned automatically on
first visit. A campaign is the user's own work, and the public ads library
lists every live campaign across all accounts - auto-creating these for every
sign-up would fill it with copies of the same seven. So this is the only way
they appear, and running it is a deliberate act.

The sample audiences the campaigns target are provisioned first if the account
does not already have them, since a campaign cannot be published without one.

Idempotent by campaign name: a campaign the account already has is left exactly
as it is, so running this twice changes nothing and never doubles the traffic.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import build_engine, build_session_factory
from src.models import Campaign, CampaignEvent
from src.repositories.audience_repository import AudienceRepository
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.enums import CampaignStatus
from src.services.audience_service import AudienceService
from src.services.campaign_service import CampaignService
from src.services.sample_campaign import (
    SAMPLE_CAMPAIGNS,
    SampleCampaign,
    campaign_payload,
    sample_events,
)


class SeedReport:
    """What one run did, so the summary is counted rather than guessed."""

    def __init__(self) -> None:
        self.created: list[str] = []
        self.skipped: list[str] = []
        self.events = 0


async def seed(owner_user_id: str) -> SeedReport:
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    report = SeedReport()

    try:
        async with session_factory() as session:
            await _ensure_audiences(session, owner_user_id)
            audiences = await _audiences_by_name(session, owner_user_id)

            for sample in SAMPLE_CAMPAIGNS:
                await _seed_one(session, sample, owner_user_id, audiences, report)
    finally:
        await engine.dispose()

    return report


async def _ensure_audiences(session: AsyncSession, owner_user_id: str) -> None:
    """Provision the sample lists if this account has none of them yet.

    The same provisioner the audience screen runs, so an account seeded here
    and an account that simply signed in end up with identical lists.
    """
    await AudienceService(AudienceRepository(session)).provision_samples(owner_user_id)


async def _audiences_by_name(
    session: AsyncSession, owner_user_id: str
) -> dict[str, tuple[str, list[str]]]:
    """Every audience this account owns, as {name: (id, member ids)}.

    Member ids are read once here rather than per campaign: events name a
    member so the analytics can tell recipient traffic from anonymous preview
    traffic, and three campaigns share the same list.
    """
    repository = AudienceRepository(session)
    audiences, _ = await repository.list_audiences(owner_user_id, limit=50)

    return {
        audience.name: (
            audience.id,
            [member.id for member in await repository.all_members(audience.id)],
        )
        for audience in audiences
    }


async def _seed_one(
    session: AsyncSession,
    sample: SampleCampaign,
    owner_user_id: str,
    audiences: dict[str, tuple[str, list[str]]],
    report: SeedReport,
) -> None:
    campaigns = CampaignRepository(session)

    if await campaigns.name_exists(owner_user_id, sample.name):
        report.skipped.append(sample.name)
        return

    now = datetime.now(UTC)
    audience_id, member_ids = audiences.get(sample.audience or "", (None, []))

    if sample.audience and audience_id is None:
        # The list this campaign targets is missing, so publishing it would
        # fail on a blocker. Say so rather than creating a broken draft.
        print(f"  ! skipped '{sample.name}': no audience named '{sample.audience}'")
        report.skipped.append(sample.name)
        return

    service = CampaignService(campaigns, EventRepository(session), AudienceRepository(session))
    created = await service.create(
        campaign_payload(sample, audience_id=audience_id, now=now), owner_user_id
    )

    await _apply_status(service, created.id, sample.status, owner_user_id)

    campaign = await campaigns.get(created.id, owner_user_id)
    if campaign is None:  # pragma: no cover - created in this session a line ago
        raise RuntimeError(f"'{sample.name}' vanished between creating and reading it back.")

    _backdate(campaign, now)

    if sample.traffic is not None:
        events = sample_events(campaign, sample.traffic, member_ids=member_ids, now=now)
        for event in events:
            session.add(CampaignEvent(**event))
        report.events += len(events)

    await session.commit()
    report.created.append(sample.name)


async def _apply_status(
    service: CampaignService, campaign_id: str, target: CampaignStatus, owner_user_id: str
) -> None:
    """Move a fresh draft to the state the sample asks for.

    PAUSED is reached the way a user reaches it - publish, then pause - because
    that is the only transition the state machine allows, and because it is
    what sets ``published_at``. SCHEDULED and COMPLETED are not requested at
    all: the server derives them from the schedule, so a future ``start_at``
    publishes as SCHEDULED and a past ``end_at`` reads as COMPLETED without
    anything being written.
    """
    if target is CampaignStatus.DRAFT:
        return

    publish_as = (
        CampaignStatus.SCHEDULED if target is CampaignStatus.SCHEDULED else CampaignStatus.ACTIVE
    )
    await service.change_status(campaign_id, publish_as, owner_user_id)

    if target is CampaignStatus.PAUSED:
        await service.change_status(campaign_id, CampaignStatus.PAUSED, owner_user_id)


def _backdate(campaign: Campaign, now: datetime) -> None:
    """Age the campaign to match its schedule.

    Everything above ran through the real services, so every row is stamped
    with this minute - which puts a campaign that has been live for a fortnight
    at the top of a dashboard sorted by date created, next to "created just
    now". These two columns are the only ones a seeder has to write directly,
    because no API lets a user set them.
    """
    if campaign.start_at is not None:
        # Two days before it started, and never in the future - a campaign
        # scheduled for next week was still created before today.
        created_at = min(campaign.start_at - timedelta(days=2), now - timedelta(days=1))
    else:
        created_at = now - timedelta(days=3)

    campaign.created_at = created_at

    if campaign.published_at is not None:
        campaign.published_at = created_at + timedelta(hours=1)

    # Ads were created with the campaign, and their order on the campaign
    # screen is their creation order - so keep it.
    for index, ad in enumerate(campaign.ads):
        ad.created_at = created_at + timedelta(seconds=index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner",
        default="user_dev",
        help="Clerk user id to own the campaigns. Match the X-Dev-User-Id you "
        "develop with, or the real Clerk id from a signed-in session.",
    )
    args = parser.parse_args()

    for sample in SAMPLE_CAMPAIGNS:
        ads = len(sample.ads)
        print(f"  {sample.name} ({ads} ad{'s' if ads != 1 else ''}, {sample.status.value})")

    report = asyncio.run(seed(args.owner))

    if report.created:
        print(
            f"\nCreated {len(report.created)} campaigns and {report.events} events "
            f"for {args.owner}."
        )
    if report.skipped:
        print(f"{len(report.skipped)} already existed and were left alone.")
    if not report.created and not report.skipped:
        print("Nothing to seed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
