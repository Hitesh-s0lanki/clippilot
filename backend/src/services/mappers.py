"""ORM -> wire schema conversion.

Kept in one place so the read contract is defined once. Controllers never
build response models field-by-field.
"""

from datetime import datetime

from src.models import Ad, AdOption, Audience, AudienceMember, Campaign
from src.schemas.ad import AdRead
from src.schemas.audience import (
    AudienceListItem,
    AudienceMemberRead,
    AudienceRead,
    AudienceSegments,
    AudienceSelection,
    SegmentBucket,
)
from src.schemas.campaign import CampaignListItem, CampaignRead
from src.schemas.common import (
    Budget,
    CampaignMetrics,
    Compliance,
    Delivery,
    PrimaryMetric,
    Schedule,
    Tracking,
)
from src.schemas.enums import (
    AdStatus,
    AgeGroup,
    CampaignObjective,
    CampaignStatus,
    EffectiveStatus,
    Gender,
    age_group_for,
)
from src.schemas.option import OptionRead
from src.services.publish_validator import collect_ad_blockers, collect_publish_blockers
from src.services.status_service import (
    derive_ad_effective_status,
    derive_badge,
    derive_effective_status,
)

# Which metric leads the analytics view, chosen by objective.
PRIMARY_METRIC_BY_OBJECTIVE: dict[CampaignObjective, tuple[str, str]] = {
    CampaignObjective.AWARENESS: ("views", "Total views"),
    CampaignObjective.ENGAGEMENT: ("interaction_rate", "Interaction rate"),
    CampaignObjective.LEAD_CAPTURE: ("positive_rate", "Positive intent"),
    CampaignObjective.CONVERSION: ("url_click_rate", "Follow-up click-through"),
    CampaignObjective.RETENTION: ("repeat_view_rate", "Repeat views"),
}


def option_to_read(option: AdOption) -> OptionRead:
    return OptionRead(
        id=option.id,
        position=option.position,
        key=option.key,
        label=option.label,
        intent=option.intent,
        follow_up_type=option.follow_up_type,
        follow_up_message=option.follow_up_message,
        follow_up_url=option.follow_up_url,
    )


def ad_to_read(ad: Ad, *, campaign_effective: EffectiveStatus | None = None) -> AdRead:
    """One ad, with its derived status and its own list of blockers.

    ``campaign_effective`` is what lets an ad report CAMPAIGN_PAUSED. When it
    is not supplied the ad is described on its own terms, which is what the
    ad-level endpoints want before the campaign has been loaded.
    """
    status = AdStatus(ad.status)

    return AdRead(
        id=ad.id,
        campaign_id=ad.campaign_id,
        name=ad.name,
        status=status,
        effective_status=derive_ad_effective_status(
            status=status,
            is_complete=ad.is_complete,
            campaign_effective=campaign_effective or EffectiveStatus.ACTIVE,
        ),
        video_url=ad.video_url,
        poster_url=ad.poster_url,
        captions_url=ad.captions_url,
        video_duration_seconds=ad.video_duration_seconds,
        headline=ad.headline,
        description=ad.description,
        personalised_message=ad.personalised_message,
        cta=ad.cta,
        options=[option_to_read(o) for o in sorted(ad.options, key=lambda x: x.position)],
        blockers=[b.field for b in collect_ad_blockers(ad)],
        created_at=ad.created_at,
        updated_at=ad.updated_at,
    )


def member_to_read(member: AudienceMember) -> AudienceMemberRead:
    return AudienceMemberRead(
        id=member.id,
        full_name=member.full_name,
        email=member.email,
        phone=member.phone,
        age=member.age,
        age_group=age_group_for(member.age),
        gender=Gender(member.gender),
        city=member.city,
        country=member.country,
        external_ref=member.external_ref,
        attributes=member.attributes,
        created_at=member.created_at,
    )


def to_buckets(counts: list[tuple[str | None, int]], total: int) -> list[SegmentBucket]:
    """Turn grouped counts into shares of the whole audience.

    A null city or country is reported as UNKNOWN rather than dropped: a
    breakdown whose slices do not add up to the audience is worse than one that
    admits how much of it is unlabelled.
    """
    return [
        SegmentBucket(
            key=key or AgeGroup.UNKNOWN.value,
            count=count,
            # Never divides by zero: an empty audience has no buckets at all.
            share=round(count / total, 4) if total else 0.0,
        )
        for key, count in counts
    ]


def audience_to_list_item(audience: Audience, *, campaign_count: int = 0) -> AudienceListItem:
    return AudienceListItem(
        id=audience.id,
        name=audience.name,
        description=audience.description,
        member_count=audience.member_count,
        campaign_count=campaign_count,
        created_at=audience.created_at,
        updated_at=audience.updated_at,
    )


def audience_to_read(
    audience: Audience, *, segments: AudienceSegments, campaign_count: int = 0
) -> AudienceRead:
    return AudienceRead(
        **audience_to_list_item(audience, campaign_count=campaign_count).model_dump(),
        segments=segments,
    )


def audience_to_selection(audience: Audience | None) -> AudienceSelection | None:
    """What a campaign says about the list it targets. Null until one is picked."""
    if audience is None:
        return None

    return AudienceSelection(
        id=audience.id,
        name=audience.name,
        member_count=audience.member_count,
    )


def build_metrics(
    counts: dict[str, int], last_activity_at: datetime | None = None
) -> CampaignMetrics:
    views = counts.get("VIEW", 0)
    interactions = counts.get("RESPONSE", 0)

    return CampaignMetrics(
        views=views,
        interactions=interactions,
        # Never divides by zero: a campaign with no views has a rate of 0.
        interaction_rate=round(interactions / views, 4) if views else 0.0,
        last_activity_at=last_activity_at,
    )


def primary_metric_for(
    objective: str, metrics: CampaignMetrics, positive_rate: float | None = None
) -> PrimaryMetric | None:
    try:
        obj = CampaignObjective(objective)
    except ValueError:
        return None

    key, label = PRIMARY_METRIC_BY_OBJECTIVE[obj]

    value = {
        "views": float(metrics.views),
        "interaction_rate": metrics.interaction_rate,
        "positive_rate": positive_rate if positive_rate is not None else 0.0,
        "url_click_rate": metrics.interaction_rate,
        "repeat_view_rate": 0.0,
    }.get(key, 0.0)

    return PrimaryMetric(key=key, label=label, value=value)


def campaign_to_read(
    campaign: Campaign,
    *,
    metrics: CampaignMetrics | None = None,
    now: datetime | None = None,
) -> CampaignRead:
    blockers = collect_publish_blockers(campaign)
    status = CampaignStatus(campaign.status)
    resolved_metrics = metrics or CampaignMetrics()
    effective = derive_effective_status(
        status=status,
        start_at=campaign.start_at,
        end_at=campaign.end_at,
        is_publishable=not blockers,
        now=now,
    )

    return CampaignRead(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        objective=campaign.objective,
        status=status,
        effective_status=effective,
        badge=derive_badge(status, campaign.published_at),
        schedule=Schedule(
            start_at=campaign.start_at,
            end_at=campaign.end_at,
            timezone=campaign.timezone,
        ),
        budget=Budget(
            budget_type=campaign.budget_type,
            budget_amount_minor=campaign.budget_amount_minor,
            currency=campaign.currency,
            spend_cap_minor=campaign.spend_cap_minor,
        ),
        delivery=Delivery(
            pacing=campaign.pacing,
            send_cap_total=campaign.send_cap_total,
            send_cap_per_day=campaign.send_cap_per_day,
            frequency_cap_per_recipient=campaign.frequency_cap_per_recipient,
        ),
        compliance=Compliance(
            special_category=campaign.special_category,
            disclaimer_text=campaign.disclaimer_text,
        ),
        tracking=Tracking(
            utm_source=campaign.utm_source,
            utm_medium=campaign.utm_medium,
            utm_campaign=campaign.utm_campaign,
            utm_content=campaign.utm_content,
            external_ref=campaign.external_ref,
        ),
        audience=audience_to_selection(campaign.audience),
        ads=[ad_to_read(ad, campaign_effective=effective) for ad in campaign.ads],
        metrics=resolved_metrics,
        publish_blockers=[b.field for b in blockers],
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        published_at=campaign.published_at,
        archived_at=campaign.archived_at,
    )


def campaign_to_list_item(
    campaign: Campaign,
    *,
    metrics: CampaignMetrics | None = None,
    now: datetime | None = None,
) -> CampaignListItem:
    status = CampaignStatus(campaign.status)
    primary = campaign.primary_ad

    return CampaignListItem(
        id=campaign.id,
        name=campaign.name,
        objective=campaign.objective,
        status=status,
        effective_status=derive_effective_status(
            status=status,
            start_at=campaign.start_at,
            end_at=campaign.end_at,
            is_publishable=not collect_publish_blockers(campaign),
            now=now,
        ),
        badge=derive_badge(status, campaign.published_at),
        poster_url=primary.poster_url if primary else None,
        ad_count=len(campaign.ads),
        live_ad_count=len(campaign.live_ads),
        audience_name=campaign.audience.name if campaign.audience else None,
        audience_size=campaign.audience.member_count if campaign.audience else 0,
        metrics=metrics or CampaignMetrics(),
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        published_at=campaign.published_at,
    )
