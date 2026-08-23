"""ORM -> wire schema conversion.

Kept in one place so the read contract is defined once. Controllers never
build response models field-by-field.
"""

from datetime import datetime

from src.models import Campaign, CampaignOption, Experience, Recipient
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
from src.schemas.enums import CampaignObjective, CampaignStatus
from src.schemas.experience import ExperienceRead
from src.schemas.option import OptionRead
from src.schemas.recipient import Audience, RecipientRead
from src.services.publish_validator import collect_publish_blockers
from src.services.status_service import derive_badge, derive_effective_status

# Which metric leads the analytics view, chosen by objective.
PRIMARY_METRIC_BY_OBJECTIVE: dict[CampaignObjective, tuple[str, str]] = {
    CampaignObjective.AWARENESS: ("views", "Total views"),
    CampaignObjective.ENGAGEMENT: ("interaction_rate", "Interaction rate"),
    CampaignObjective.LEAD_CAPTURE: ("positive_rate", "Positive intent"),
    CampaignObjective.CONVERSION: ("url_click_rate", "Follow-up click-through"),
    CampaignObjective.RETENTION: ("repeat_view_rate", "Repeat views"),
}


def option_to_read(option: CampaignOption) -> OptionRead:
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


def experience_to_read(experience: Experience | None) -> ExperienceRead | None:
    if experience is None:
        return None

    return ExperienceRead(
        id=experience.id,
        video_url=experience.video_url,
        poster_url=experience.poster_url,
        captions_url=experience.captions_url,
        video_duration_seconds=experience.video_duration_seconds,
        headline=experience.headline,
        personalised_message=experience.personalised_message,
        options=[option_to_read(o) for o in sorted(experience.options, key=lambda x: x.position)],
    )


def recipient_to_read(recipient: Recipient) -> RecipientRead:
    return RecipientRead(
        id=recipient.id,
        customer_name=recipient.customer_name,
        email=recipient.email,
        phone=recipient.phone,
        external_ref=recipient.external_ref,
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

    return CampaignRead(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        objective=campaign.objective,
        status=status,
        effective_status=derive_effective_status(
            status=status,
            start_at=campaign.start_at,
            end_at=campaign.end_at,
            is_publishable=not blockers,
            now=now,
        ),
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
        audience=Audience(
            audience_type=campaign.audience_type,
            recipient_count=len(campaign.recipients),
            recipients=[recipient_to_read(r) for r in campaign.recipients],
        ),
        experience=experience_to_read(campaign.experience),
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
    experience = campaign.experience

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
        poster_url=experience.poster_url if experience else None,
        recipient_count=len(campaign.recipients),
        metrics=metrics or CampaignMetrics(),
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        published_at=campaign.published_at,
    )
