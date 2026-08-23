"""Seed demo campaigns, each with its ads, for one account.

    uv run python -m scripts.seed_campaigns --owner user_2abc...

Written to make a demo database look like an account somebody has actually
used, rather than four copies of the same row: the campaigns sit at different
points of the lifecycle, hold between one and three creatives, and share the
seeded audiences the way real campaigns share a list. One ad is deliberately
left without a video so the INCOMPLETE state and the publish blockers have
something to describe.

The videos are real, public, CC0-licensed files, so the preview and the
recipient page actually play something. A fake `cdn.example.com` URL passes
validation and then shows a broken player, which is a worse demo than none.

Idempotent: a campaign whose name the account already has is left exactly as it
is, so running this twice does not duplicate anything. It needs the audiences
to exist first - run `scripts.seed_audiences` if the account has none.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass, field

from src.core.config import get_settings
from src.core.database import build_engine, build_session_factory
from src.repositories.audience_repository import AudienceRepository
from src.repositories.campaign_repository import CampaignRepository
from src.repositories.event_repository import EventRepository
from src.schemas.ad import AdInput
from src.schemas.campaign import CampaignCreate
from src.schemas.common import Budget, Compliance, Schedule, Tracking
from src.schemas.enums import CampaignStatus
from src.schemas.option import OptionInput
from src.services.campaign_service import CampaignService

# Real CC0 files. Checked reachable rather than assumed - see the module note.
FLOWER = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
FRIDAY = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/friday.mp4"
BUNNY = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
SINTEL = "https://test-videos.co.uk/vids/sintel/mp4/h264/360/Sintel_360_10s_1MB.mp4"
JELLYFISH = "https://test-videos.co.uk/vids/jellyfish/mp4/h264/360/Jellyfish_360_10s_1MB.mp4"


def poster(seed: str) -> str:
    """A stable placeholder image, different per ad so cards are distinguishable."""
    return f"https://picsum.photos/seed/{seed}/800/450.jpg"


def options(positive: str, negative: str, reply: str) -> list[OptionInput]:
    """The brief's two buttons: one that advances, one that declines."""
    return [
        OptionInput(
            position=1,
            label=positive,
            intent="POSITIVE",
            follow_up_type="MESSAGE",
            follow_up_message=reply,
        ),
        OptionInput(
            position=2,
            label=negative,
            intent="NEGATIVE",
            follow_up_type="MESSAGE",
            follow_up_message="No problem, {{customer_name}}. We won't follow up on this one.",
        ),
    ]


@dataclass(frozen=True)
class Seed:
    """One campaign to create, and what to do with it afterwards."""

    payload: CampaignCreate
    audience: str
    publish: bool = False
    #: Ads to switch off again after publishing, by name. Publishing activates
    #: every complete draft, and a campaign where one creative is paused is a
    #: more interesting demo than one where they all run.
    pause: tuple[str, ...] = field(default_factory=tuple)


def build_seeds() -> list[Seed]:
    return [
        Seed(
            audience="HNI Investors - Metro",
            publish=True,
            pause=("Fee transparency angle",),
            payload=CampaignCreate(
                name="Portfolio review invite",
                description="Quarterly review push for the metro HNI book.",
                objective="LEAD_CAPTURE",
                compliance=Compliance(
                    special_category="FINANCIAL_PRODUCTS_SERVICES",
                    disclaimer_text=(
                        "Investments are subject to market risk. Read all scheme-related "
                        "documents carefully. This is not investment advice."
                    ),
                ),
                budget=Budget(budget_type="LIFETIME", budget_amount_minor=7_500_00, currency="INR"),
                schedule=Schedule(timezone="Asia/Kolkata"),
                tracking=Tracking(utm_campaign="portfolio-review", utm_content="q3-invite"),
                ads=[
                    AdInput(
                        name="Advisor call angle",
                        video_url=FLOWER,
                        poster_url=poster("portfolio-advisor"),
                        headline="Your portfolio, reviewed by a human",
                        description="Thirty minutes with the advisor who knows your holdings.",
                        cta="BOOK_NOW",
                        personalised_message=(
                            "Hi {{customer_name}}, it has been a quarter since we last looked "
                            "at your portfolio together. Shall we book that review?"
                        ),
                        options=options(
                            "Book my review",
                            "Not this quarter",
                            "Booked, {{customer_name}} - your advisor will confirm a slot today.",
                        ),
                    ),
                    AdInput(
                        name="Fee transparency angle",
                        video_url=BUNNY,
                        poster_url=poster("portfolio-fees"),
                        headline="What you actually paid last quarter",
                        description="A plain breakdown, before we talk about anything else.",
                        cta="LEARN_MORE",
                        personalised_message=(
                            "{{customer_name}}, here is exactly what you paid in fees last "
                            "quarter, and what it bought you."
                        ),
                        options=options(
                            "Show me the breakdown",
                            "Maybe later",
                            "On its way, {{customer_name}} - check your inbox in a minute.",
                        ),
                    ),
                ],
            ),
        ),
        Seed(
            audience="Lapsed Policyholders",
            publish=True,
            payload=CampaignCreate(
                name="Policy renewal nudge",
                description="Win back policies that lapsed in the last two quarters.",
                objective="RETENTION",
                compliance=Compliance(
                    special_category="FINANCIAL_PRODUCTS_SERVICES",
                    disclaimer_text=(
                        "Terms and conditions apply. Cover resumes only once the renewal "
                        "premium is received."
                    ),
                ),
                schedule=Schedule(timezone="Asia/Kolkata"),
                tracking=Tracking(utm_campaign="policy-renewal", utm_content="lapsed-q2"),
                ads=[
                    AdInput(
                        name="Cost of the gap",
                        video_url=SINTEL,
                        poster_url=poster("policy-gap"),
                        headline="You are not covered right now",
                        description="Restarting takes two minutes and no new paperwork.",
                        cta="GET_QUOTE",
                        personalised_message=(
                            "{{customer_name}}, your policy lapsed in March - which means "
                            "you are uncovered today. Restarting is two minutes."
                        ),
                        options=options(
                            "Restart my cover",
                            "Not right now",
                            "Thanks {{customer_name}} - we have sent the renewal link.",
                        ),
                    ),
                ],
            ),
        ),
        Seed(
            audience="Mutual Fund Prospects",
            payload=CampaignCreate(
                name="SIP top-up for Q3",
                description="Encourage existing SIPs to step up before the quarter ends.",
                objective="CONVERSION",
                compliance=Compliance(
                    special_category="FINANCIAL_PRODUCTS_SERVICES",
                    disclaimer_text=(
                        "Investments are subject to market risk. Past performance does not "
                        "guarantee future returns."
                    ),
                ),
                budget=Budget(budget_type="DAILY", budget_amount_minor=2_000_00, currency="INR"),
                schedule=Schedule(timezone="Asia/Kolkata"),
                tracking=Tracking(utm_campaign="sip-top-up"),
                ads=[
                    AdInput(
                        name="Small step-up",
                        video_url=JELLYFISH,
                        poster_url=poster("sip-stepup"),
                        headline="500 more a month",
                        description="The smallest change that still compounds.",
                        cta="SIGN_UP",
                        personalised_message=(
                            "Hi {{customer_name}}, adding 500 a month to your SIP now is "
                            "worth more than adding 5,000 next year."
                        ),
                        options=options(
                            "Step up my SIP",
                            "Keep it as it is",
                            "Done, {{customer_name}} - the change applies from next month.",
                        ),
                    ),
                    # Deliberately unfinished: no video. This is what gives the
                    # ads screen an INCOMPLETE row and the campaign a publish
                    # blocker to point at.
                    AdInput(
                        name="Compounding explainer",
                        headline="Ten years, two SIPs",
                        description="What the difference actually looks like.",
                        cta="LEARN_MORE",
                        personalised_message=(
                            "{{customer_name}}, here is the same money invested two ways."
                        ),
                        options=options(
                            "Show me",
                            "Not now",
                            "Sent, {{customer_name}} - it is a two-minute read.",
                        ),
                    ),
                ],
            ),
        ),
        Seed(
            audience="HNI Investors - Metro",
            payload=CampaignCreate(
                name="Diwali offer teaser",
                description="Seasonal teaser. Creative still being written.",
                objective="AWARENESS",
                schedule=Schedule(timezone="Asia/Kolkata"),
                tracking=Tracking(utm_campaign="diwali-teaser"),
                ads=[
                    AdInput(
                        name="Festive teaser",
                        video_url=FRIDAY,
                        poster_url=poster("diwali-teaser"),
                        headline="Something for the festive quarter",
                        cta="GET_OFFER",
                        personalised_message=(
                            "{{customer_name}}, we are putting something together for "
                            "Diwali. Want to hear it first?"
                        ),
                        options=options(
                            "Tell me first",
                            "No thanks",
                            "You are on the list, {{customer_name}}.",
                        ),
                    ),
                ],
            ),
        ),
    ]


async def seed(owner_user_id: str) -> tuple[int, int, list[str]]:
    """Create the campaigns this account is missing. Returns (campaigns, ads, skipped)."""
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)

    created = ads = 0
    skipped: list[str] = []

    try:
        async with session_factory() as session:
            campaigns = CampaignRepository(session)
            audiences = AudienceRepository(session)
            service = CampaignService(campaigns, EventRepository(session), audiences)

            by_name = {
                audience.name: audience.id
                for audience in (await audiences.list_audiences(owner_user_id, limit=100))[0]
            }

            for item in build_seeds():
                name = item.payload.name

                if await campaigns.name_exists(owner_user_id, name):
                    skipped.append(name)
                    continue

                audience_id = by_name.get(item.audience)
                if audience_id is None:
                    skipped.append(f"{name} (no audience {item.audience!r})")
                    continue

                payload = item.payload.model_copy(update={"audience_id": audience_id})
                campaign = await service.create(payload, owner_user_id)
                created += 1
                ads += len(campaign.ads)

                if item.publish:
                    campaign = await service.change_status(
                        campaign.id, CampaignStatus.ACTIVE, owner_user_id
                    )
                    for ad in campaign.ads:
                        if ad.name in item.pause:
                            await _pause(session, campaign.id, ad.id, owner_user_id)

            return created, ads, skipped
    finally:
        await engine.dispose()


async def _pause(session, campaign_id: str, ad_id: str, owner_user_id: str) -> None:
    """Switch one ad back off, so a published campaign has a paused creative."""
    from src.schemas.enums import AdStatus
    from src.services.ad_service import AdService

    service = AdService(CampaignRepository(session), EventRepository(session))
    await service.change_status(campaign_id, ad_id, AdStatus.PAUSED, owner_user_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner",
        default="user_dev",
        help="Clerk user id to own the campaigns. Match the X-Dev-User-Id you "
        "develop with, or the real Clerk id from a signed-in session.",
    )
    args = parser.parse_args()

    created, ads, skipped = asyncio.run(seed(args.owner))

    for name in skipped:
        print(f"  skipped {name}")

    if created == 0:
        print(f"{args.owner} already has these campaigns. Nothing to do.")
    else:
        print(f"Created {created} campaigns and {ads} ads for {args.owner}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
