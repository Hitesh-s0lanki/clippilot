"""The sample campaigns a demo account is seeded with.

Seven campaigns built over the nine videos published on strique.io - eight ad
creatives under ``/ad examples/`` plus the sixty-second platform tour. They
exist so a demo lands on a dashboard that has something to say: a spread of
objectives, every lifecycle state the model can be in, single- and multi-ad
campaigns, both follow-up types, and enough recorded traffic for the analytics
screen to draw real bars.

Two things are deliberate:

**The copy matches what is on screen.** Each ad is written to the video it
plays - the watch ad talks about a watch, the silent unboxing asks whether the
silence worked. Lorem-ipsum demo data proves the tables render; it does not
prove the product reads well, which is the thing a demo is for.

**One campaign is left half-built.** ``Strique Platform - Product Tour`` has a
video and one option and no audience, so ``INCOMPLETE``, the per-ad blockers
and the disabled Publish button all have something to show. A seed where
everything is finished hides half the builder.

Videos are referenced at their public strique.io URLs rather than copied: they
are already served over https with the right content type, which is exactly
what ``validate_video_url`` asks of a video URL.

Consumed by ``scripts.seed_campaigns``. Nothing here imports the ORM - the
catalogue describes campaigns, the seeder creates them.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.schemas.ad import AdInput
from src.schemas.campaign import CampaignCreate
from src.schemas.common import Budget, Compliance, Delivery, Schedule, Tracking
from src.schemas.enums import (
    BudgetType,
    CallToAction,
    CampaignObjective,
    CampaignStatus,
    EventType,
    FollowUpType,
    OptionIntent,
)
from src.schemas.option import OptionInput
from src.schemas.validators import slugify

# Deterministic: the same account always gets the same traffic, so a screenshot
# taken today still matches the analytics screen tomorrow.
SEED = 20260823

MEDIA_BASE = "https://www.strique.io"

# The demo tenant's own site. Follow-up URLs point here rather than at the
# advertised brands' real domains: a seeded click should land somewhere that
# belongs to whoever is running the demo.
DESTINATION = "https://www.strique.io/"


# Rupees, as the minor units the model insists on. Written through a helper so
# a budget in the catalogue below reads as money instead of as six zeroes.
def rupees(amount: int) -> int:
    """Whole rupees to paise."""
    return amount * 100


def ad_video(slug: str) -> str:
    """One of the ad creatives published under strique.io/ad examples/."""
    return f"{MEDIA_BASE}/ad%20examples/{slug}.mp4"


USER_AGENTS = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0",
)


# --- the shape of one sample ------------------------------------------------


@dataclass(frozen=True, slots=True)
class SampleTraffic:
    """How much history to invent for one campaign.

    Rates rather than counts, so the funnel stays coherent when a number is
    tuned: responses are always a subset of the sessions that viewed, and a
    positive click is always one of the two options that ad actually owns.
    """

    sessions: int
    response_rate: float
    positive_share: float
    # Preview traffic that arrived on a link naming nobody. Real campaigns have
    # some; without it every event has a member and the anonymous path in the
    # analytics never gets exercised.
    anonymous_share: float = 0.2


@dataclass(frozen=True, slots=True)
class SampleCampaign:
    """One campaign to create, and what to do with it once it exists."""

    name: str
    description: str
    objective: CampaignObjective
    # Name of the sample audience to target. None leaves the campaign without
    # one, which is itself a publish blocker worth demonstrating.
    audience: str | None
    # Where to leave it. DRAFT means "created and not published".
    status: CampaignStatus
    ads: tuple[AdInput, ...]
    # Days from now. Negative is in the past; None leaves the field null.
    starts_in_days: int | None = None
    ends_in_days: int | None = None
    timezone: str = "Asia/Kolkata"
    budget: Budget = field(default_factory=Budget)
    delivery: Delivery = field(default_factory=Delivery)
    external_ref: str | None = None
    traffic: SampleTraffic | None = None


def option(
    position: int,
    label: str,
    intent: OptionIntent,
    *,
    message: str | None = None,
    url: str | None = None,
) -> OptionInput:
    """One response button, typed by which follow-up it was given."""
    return OptionInput(
        position=position,
        label=label,
        intent=intent,
        follow_up_type=FollowUpType.URL if url else FollowUpType.MESSAGE,
        follow_up_message=message,
        follow_up_url=url,
    )


# --- the catalogue ----------------------------------------------------------

SAMPLE_CAMPAIGNS: tuple[SampleCampaign, ...] = (
    SampleCampaign(
        name="Sylvi Chronograph - Festive Drop",
        description=(
            "Sample data. Festive push for the analog-digital chronograph. One vertical "
            "hero cut, aimed at the metro high-value list."
        ),
        objective=CampaignObjective.CONVERSION,
        audience="HNI Investors - Metro",
        status=CampaignStatus.ACTIVE,
        starts_in_days=-12,
        budget=Budget(
            budget_type=BudgetType.DAILY,
            budget_amount_minor=rupees(5_000),
            spend_cap_minor=rupees(120_000),
        ),
        delivery=Delivery(send_cap_total=40, send_cap_per_day=8),
        external_ref="SEED-SYLVI-FESTIVE",
        ads=(
            AdInput(
                name="Wrist hero - 8s vertical",
                video_url=ad_video("ad-1"),
                video_duration_seconds=8,
                headline="The festive drop, on the wrist in eight seconds",
                description=(
                    "Sylvi's analog-digital chronograph in brushed steel on tan leather, "
                    "shot on the wrist in daylight. Limited festive run."
                ),
                personalised_message=(
                    "Hi {{customer_name}}, we set one aside for you in {{city}}. Eight "
                    "seconds is all it takes to see why this one goes first."
                ),
                cta=CallToAction.SHOP_NOW,
                options=[
                    option(1, "Show me the drop", OptionIntent.POSITIVE, url=DESTINATION),
                    option(
                        2,
                        "Not this time",
                        OptionIntent.NEGATIVE,
                        message=(
                            "No problem, {{first_name}}. We'll hold your place for the next "
                            "drop and stay out of your inbox until then."
                        ),
                    ),
                ],
            ),
        ),
        traffic=SampleTraffic(sessions=148, response_rate=0.34, positive_share=0.62),
    ),
    SampleCampaign(
        name="Air Dior - Unbox in Silence",
        description=(
            "Sample data. Eight-second silent unboxing, run as a reaction test rather "
            "than a sales push - the two buttons are the question."
        ),
        objective=CampaignObjective.ENGAGEMENT,
        audience="HNI Investors - Metro",
        status=CampaignStatus.ACTIVE,
        starts_in_days=-9,
        external_ref="SEED-DIOR-SILENCE",
        ads=(
            AdInput(
                name="Silent unboxing - 8s vertical",
                video_url=ad_video("ad-2"),
                video_duration_seconds=8,
                headline="No music. No voiceover. Just the box.",
                description=(
                    "The Air Dior box opened in full silence - tissue, lid, and nothing "
                    "else on the track."
                ),
                personalised_message=(
                    "Hi {{customer_name}}, watch this one with the sound on. Eight seconds, "
                    "no music, and we want to know whether it worked on you."
                ),
                cta=CallToAction.LEARN_MORE,
                options=[
                    option(
                        1,
                        "It worked - show me more",
                        OptionIntent.POSITIVE,
                        message=(
                            "Thanks {{first_name}}. We're cutting three more in the same "
                            "silent format, and you'll get the next one first."
                        ),
                    ),
                    option(
                        2,
                        "Needed sound",
                        OptionIntent.NEGATIVE,
                        message=(
                            "Noted, {{first_name}} - that's exactly the read we were after. "
                            "The next cut gets a score."
                        ),
                    ),
                ],
            ),
        ),
        traffic=SampleTraffic(sessions=212, response_rate=0.41, positive_share=0.55),
    ),
    SampleCampaign(
        name="Festive Gifting - Fragrance & Capsule",
        description=(
            "Sample data. Two creatives against one gifting brief: a vertical fragrance "
            "cut and a widescreen capsule showcase. The A/B this data model exists for."
        ),
        objective=CampaignObjective.LEAD_CAPTURE,
        audience="HNI Investors - Metro",
        status=CampaignStatus.ACTIVE,
        starts_in_days=-18,
        ends_in_days=10,
        budget=Budget(
            budget_type=BudgetType.LIFETIME,
            budget_amount_minor=rupees(250_000),
            spend_cap_minor=rupees(250_000),
        ),
        delivery=Delivery(send_cap_total=40, frequency_cap_per_recipient=2),
        external_ref="SEED-GIFTING-Q4",
        ads=(
            AdInput(
                name="Kylie signature scent - 9:16",
                video_url=ad_video("ad-3"),
                video_duration_seconds=12,
                headline="The scent she keeps on the dressing table",
                description=(
                    "The Kylie bottle unboxed at a vanity in morning light, then left "
                    "where it will actually live."
                ),
                personalised_message=(
                    "Hi {{first_name}}, this is the one we'd wrap first this season. Tell "
                    "us who it's for and we'll put the box together."
                ),
                cta=CallToAction.GET_OFFER,
                options=[
                    option(1, "Send me the gifting edit", OptionIntent.POSITIVE, url=DESTINATION),
                    option(
                        2,
                        "Not gifting this year",
                        OptionIntent.NEGATIVE,
                        message=(
                            "Understood, {{first_name}}. We'll keep the edit for next season "
                            "and leave your inbox alone."
                        ),
                    ),
                ],
            ),
            AdInput(
                name="ALORA capsule - 16:9 showcase",
                video_url=ad_video("ad-10"),
                video_duration_seconds=12,
                headline="Four pieces. One capsule. ALORA.",
                description=(
                    "Fragrance, denim, gold and heels turning inside lit glass cases - the "
                    "whole capsule in twelve seconds."
                ),
                personalised_message=(
                    "Hi {{customer_name}}, the ALORA capsule lands in {{city}} this week. Four "
                    "pieces, one box, and we'd like your read on it."
                ),
                cta=CallToAction.BOOK_NOW,
                options=[
                    option(
                        1,
                        "Book a preview",
                        OptionIntent.POSITIVE,
                        message=(
                            "Done, {{first_name}}. A stylist will call to fix a slot for the "
                            "ALORA preview in {{city}}."
                        ),
                    ),
                    option(
                        2,
                        "Just browsing",
                        OptionIntent.NEGATIVE,
                        message=(
                            "That's fine, {{first_name}} - the capsule stays online all month "
                            "if you change your mind."
                        ),
                    ),
                ],
            ),
        ),
        traffic=SampleTraffic(sessions=264, response_rate=0.29, positive_share=0.48),
    ),
    SampleCampaign(
        name="Chemistry Denim - Winter Re-engagement",
        description=(
            "Sample data. Win-back for the lapsed list, paused after a fortnight when "
            "the response rate would not lift. Left paused on purpose."
        ),
        objective=CampaignObjective.RETENTION,
        audience="Lapsed Policyholders",
        status=CampaignStatus.PAUSED,
        starts_in_days=-26,
        budget=Budget(
            budget_type=BudgetType.DAILY,
            budget_amount_minor=rupees(2_000),
            spend_cap_minor=rupees(40_000),
        ),
        external_ref="SEED-CHEMISTRY-WINBACK",
        ads=(
            AdInput(
                name="Denim shirt dress - creator cut",
                video_url=ad_video("ad-5"),
                video_duration_seconds=12,
                headline="The denim shirt dress is back in your size",
                description=(
                    "Chemistry's embroidered denim shirt dress, filmed as a straight "
                    "try-on rather than a studio shot."
                ),
                personalised_message=(
                    "It's been a while, {{customer_name}}. The denim shirt dress you looked "
                    "at is back in stock in {{city}} - here's how it actually moves."
                ),
                cta=CallToAction.SHOP_NOW,
                options=[
                    option(
                        1,
                        "Hold one for me",
                        OptionIntent.POSITIVE,
                        message=(
                            "Held, {{first_name}}. We'll keep it for 48 hours and text you a "
                            "pickup slot in {{city}}."
                        ),
                    ),
                    option(
                        2,
                        "Take me off this list",
                        OptionIntent.NEGATIVE,
                        message=(
                            "Done, {{first_name}}. You won't hear from us about this one again."
                        ),
                    ),
                ],
            ),
        ),
        traffic=SampleTraffic(sessions=96, response_rate=0.22, positive_share=0.37),
    ),
    SampleCampaign(
        name="Night Streets - Footwear Season Launch",
        description=(
            "Sample data. Season film plus a placement reel, scheduled for next week. "
            "Published with a future start date, so it sits in SCHEDULED."
        ),
        objective=CampaignObjective.AWARENESS,
        audience="Mutual Fund Prospects",
        status=CampaignStatus.SCHEDULED,
        starts_in_days=6,
        ends_in_days=34,
        budget=Budget(
            budget_type=BudgetType.LIFETIME,
            budget_amount_minor=rupees(400_000),
            spend_cap_minor=rupees(400_000),
        ),
        delivery=Delivery(send_cap_total=35, send_cap_per_day=5),
        external_ref="SEED-FOOTWEAR-LAUNCH",
        ads=(
            AdInput(
                name="Wet asphalt - cinematic 16:9",
                video_url=ad_video("ad-7"),
                video_duration_seconds=12,
                headline="Neon, rain, and a pair that doesn't care",
                description=(
                    "Twelve seconds of a night walk shot low on wet asphalt. No copy, no "
                    "logo - the shoe carries it."
                ),
                personalised_message=(
                    "Hi {{customer_name}}, the season film drops next week. You're on the list "
                    "that sees it first."
                ),
                cta=CallToAction.LEARN_MORE,
                options=[
                    option(
                        1,
                        "Notify me at launch",
                        OptionIntent.POSITIVE,
                        message=(
                            "You're on it, {{first_name}}. We'll send the film the morning it "
                            "goes live."
                        ),
                    ),
                    option(
                        2,
                        "Skip this one",
                        OptionIntent.NEGATIVE,
                        message="No problem, {{first_name}} - we'll sit this season out with you.",
                    ),
                ],
            ),
            AdInput(
                name="Billboard placements - silent cut",
                video_url=ad_video("ad-9"),
                video_duration_seconds=12,
                headline="The same sandal, on four different streets",
                description=(
                    "A placement reel - beach, mall, neon high street, highway. Silent by "
                    "design, for feeds that autoplay muted."
                ),
                personalised_message=(
                    "Hi {{first_name}}, same product, four placements. Tell us which street "
                    "you would actually stop on."
                ),
                cta=CallToAction.LEARN_MORE,
                options=[
                    option(
                        1,
                        "The neon one",
                        OptionIntent.POSITIVE,
                        message=(
                            "Noted, {{first_name}}. The neon cut is ahead so far - we'll send "
                            "you the final edit."
                        ),
                    ),
                    option(
                        2,
                        "None of them",
                        OptionIntent.NEGATIVE,
                        message=(
                            "Fair, {{first_name}}. That's a useful read, and there's still "
                            "time to reshoot before launch."
                        ),
                    ),
                ],
            ),
        ),
    ),
    SampleCampaign(
        name="9yards Studio - Founder Outreach",
        description=(
            "Sample data. Creator-led B2B outreach that ran for five weeks and ended "
            "twelve days ago. Its window has closed, so it reads COMPLETED."
        ),
        objective=CampaignObjective.LEAD_CAPTURE,
        audience="Mutual Fund Prospects",
        status=CampaignStatus.ACTIVE,
        starts_in_days=-47,
        ends_in_days=-12,
        budget=Budget(
            budget_type=BudgetType.LIFETIME,
            budget_amount_minor=rupees(150_000),
            spend_cap_minor=rupees(150_000),
        ),
        delivery=Delivery(send_cap_total=35),
        external_ref="SEED-9YARDS-FOUNDERS",
        ads=(
            AdInput(
                name="Founder to founder - creator cut",
                video_url=ad_video("ad-4"),
                video_duration_seconds=12,
                headline="Got a startup idea? Here's the team for it.",
                description=(
                    "A founder-to-founder pitch for 9yards: strategy, branding and UI/UX "
                    "on demand, straight to camera."
                ),
                personalised_message=(
                    "Hi {{customer_name}}, if the idea is still sitting in a notes app, this is "
                    "the twelve seconds that gets it out. Strategy, branding and UI/UX, on "
                    "demand."
                ),
                cta=CallToAction.BOOK_NOW,
                options=[
                    option(1, "Book a 15-minute call", OptionIntent.POSITIVE, url=DESTINATION),
                    option(
                        2,
                        "Not building right now",
                        OptionIntent.NEGATIVE,
                        message=(
                            "All good, {{first_name}}. We'll check back when you are, and "
                            "nothing in between."
                        ),
                    ),
                ],
            ),
        ),
        traffic=SampleTraffic(sessions=318, response_rate=0.36, positive_share=0.58),
    ),
    SampleCampaign(
        name="Strique Platform - Product Tour",
        description=(
            "Sample data, left half-built on purpose: the sixty-second tour is in, the "
            "second button and the audience are not. This is what INCOMPLETE looks like."
        ),
        objective=CampaignObjective.AWARENESS,
        audience=None,
        status=CampaignStatus.DRAFT,
        external_ref="SEED-STRIQUE-TOUR",
        ads=(
            AdInput(
                name="Full product tour - 60s",
                video_url=f"{MEDIA_BASE}/website-hero-video.mp4",
                video_duration_seconds=59,
                headline="The agentic AI that runs the whole growth stack",
                description=(
                    "A minute inside Strique: brand DNA, product catalogue, audience "
                    "build, and the ads it ships at the end of it."
                ),
                personalised_message=(
                    "Hi {{customer_name}}, here's the full tour - sixty seconds, no slides. Ask "
                    "it for a campaign and watch it build one."
                ),
                cta=CallToAction.SIGN_UP,
                options=[
                    option(1, "See it on my account", OptionIntent.POSITIVE, url=DESTINATION),
                    # Option 2 is missing, and so is the audience. Both are real
                    # publish blockers, which is the whole point of this row.
                ],
            ),
        ),
    ),
)


# --- turning one sample into a payload --------------------------------------


def _at(now: datetime, days: int | None) -> datetime | None:
    return None if days is None else now + timedelta(days=days)


def campaign_payload(
    sample: SampleCampaign, *, audience_id: str | None, now: datetime | None = None
) -> CampaignCreate:
    """The ``CampaignCreate`` body for one sample, with its ads inline.

    Built here rather than stored in the catalogue because the schedule is
    relative: a campaign that started twelve days ago has to mean twelve days
    before the seeder ran, not before the module was imported.
    """
    moment = now or datetime.now(UTC)

    return CampaignCreate(
        name=sample.name,
        description=sample.description,
        objective=sample.objective,
        audience_id=audience_id,
        schedule=Schedule(
            start_at=_at(moment, sample.starts_in_days),
            end_at=_at(moment, sample.ends_in_days),
            timezone=sample.timezone,
        ),
        budget=sample.budget,
        delivery=sample.delivery,
        compliance=Compliance(),
        tracking=Tracking(external_ref=sample.external_ref),
        ads=list(sample.ads),
    )


# --- inventing the traffic --------------------------------------------------


def sample_events(
    campaign, traffic: SampleTraffic, *, member_ids: list[str], now: datetime | None = None
) -> list[dict]:
    """Build one campaign's worth of view and response events.

    Takes the created campaign rather than the sample, because an event needs
    the ids the database has just handed out. Returns plain dicts so this stays
    free of the ORM; the seeder is what turns them into rows.

    The funnel is generated, not fabricated: every response belongs to a
    session that viewed first, on the same ad, for the same member, a few
    seconds later. Counting distinct sessions or joining responses back to
    views therefore gives the same answer here as it would on real traffic.

    Seeded from the campaign's name, so re-seeding a database reproduces the
    same numbers and adding a campaign does not reshuffle the others.
    """
    moment = now or datetime.now(UTC)
    rng = random.Random(SEED + sum(ord(char) for char in campaign.name))

    # Only ads a recipient could actually have opened. Weighted by position:
    # a campaign's first creative carries most of its delivery.
    ads = [ad for ad in campaign.ads if ad.is_complete]
    if not ads:
        return []
    weights = [1.0 / (index + 1.6) for index in range(len(ads))]

    start, end = _traffic_window(campaign, moment)
    span = max((end - start).total_seconds(), 1.0)
    slug = slugify(campaign.name, max_length=40)

    events: list[dict] = []

    for index in range(traffic.sessions):
        ad = rng.choices(ads, weights=weights)[0]
        options = sorted(ad.options, key=lambda o: o.position)
        session_id = f"seed-{slug}-{index:04d}"
        member_id = (
            None
            if not member_ids or rng.random() < traffic.anonymous_share
            else rng.choice(member_ids)
        )
        viewed_at = start + timedelta(seconds=rng.random() * span)
        user_agent = rng.choice(USER_AGENTS)

        events.append(
            {
                "campaign_id": campaign.id,
                "ad_id": ad.id,
                "member_id": member_id,
                "session_id": session_id,
                "type": EventType.VIEW.value,
                "occurred_at": viewed_at,
                "user_agent": user_agent,
            }
        )

        if rng.random() >= traffic.response_rate:
            continue

        chosen = options[0] if rng.random() < traffic.positive_share else options[-1]
        events.append(
            {
                "campaign_id": campaign.id,
                "ad_id": ad.id,
                "member_id": member_id,
                "option_id": chosen.id,
                "session_id": session_id,
                "type": EventType.RESPONSE.value,
                # Long enough to have watched something, short enough to be the
                # same visit.
                "occurred_at": viewed_at + timedelta(seconds=rng.randint(4, 90)),
                "user_agent": user_agent,
            }
        )

    return events


def _traffic_window(campaign, now: datetime) -> tuple[datetime, datetime]:
    """When this campaign could have been watched.

    Clamped to the present at both ends: a campaign that ended a fortnight ago
    must not have activity dated yesterday, and one still running must not have
    any dated tomorrow.
    """
    start = campaign.start_at or (now - timedelta(days=14))
    end = min(campaign.end_at or now, now)

    if end <= start:
        end = start + timedelta(hours=1)

    return start, end
