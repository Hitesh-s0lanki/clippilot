"""Campaign lifecycle: derived status, dashboard badge and legal transitions.

``status`` is what the user chose and is persisted. ``effective_status`` is
derived per request from status + schedule + completeness, so no scheduler
process is needed for a campaign to become ACTIVE when its start time passes
or COMPLETED when it ends.
"""

from datetime import UTC, datetime

from src.schemas.enums import (
    ALLOWED_AD_TRANSITIONS,
    PUBLISHED_STATUSES,
    AdEffectiveStatus,
    AdStatus,
    CampaignBadge,
    CampaignStatus,
    EffectiveStatus,
)

# Which statuses a user may move to from a given status. Time-driven moves
# (SCHEDULED -> ACTIVE -> COMPLETED) are derived, not requested, so they are
# absent here.
ALLOWED_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset(
        {CampaignStatus.SCHEDULED, CampaignStatus.ACTIVE, CampaignStatus.ARCHIVED}
    ),
    CampaignStatus.SCHEDULED: frozenset(
        {CampaignStatus.PAUSED, CampaignStatus.DRAFT, CampaignStatus.ARCHIVED}
    ),
    CampaignStatus.ACTIVE: frozenset(
        {CampaignStatus.PAUSED, CampaignStatus.DRAFT, CampaignStatus.ARCHIVED}
    ),
    CampaignStatus.PAUSED: frozenset(
        {CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED, CampaignStatus.ARCHIVED}
    ),
    CampaignStatus.COMPLETED: frozenset({CampaignStatus.ARCHIVED}),
    CampaignStatus.ARCHIVED: frozenset(),
}

# Transitions back to DRAFT are an unpublish, allowed only while no events exist.
UNPUBLISH_TARGET = CampaignStatus.DRAFT


def derive_effective_status(
    *,
    status: CampaignStatus,
    start_at: datetime | None,
    end_at: datetime | None,
    is_publishable: bool,
    now: datetime | None = None,
) -> EffectiveStatus:
    """Compute the status the campaign is actually in right now."""
    moment = now or datetime.now(UTC)

    if status is CampaignStatus.ARCHIVED:
        return EffectiveStatus.ARCHIVED
    if status is CampaignStatus.DRAFT:
        return EffectiveStatus.DRAFT if is_publishable else EffectiveStatus.INCOMPLETE
    if status is CampaignStatus.PAUSED:
        return EffectiveStatus.PAUSED

    # Published family: the schedule decides.
    if end_at is not None and moment >= end_at:
        return EffectiveStatus.COMPLETED
    if start_at is not None and moment < start_at:
        return EffectiveStatus.SCHEDULED
    if status is CampaignStatus.COMPLETED:
        return EffectiveStatus.COMPLETED

    return EffectiveStatus.ACTIVE


def derive_badge(status: CampaignStatus, published_at: datetime | None = None) -> CampaignBadge:
    """The two-value badge the brief mandates for the dashboard.

    ARCHIVED sits in neither the Draft nor the Published set, so it falls back
    to whether the campaign was ever published. Without that, archiving a live
    campaign would relabel it "Draft", which reads as though it never ran.
    """
    if status in PUBLISHED_STATUSES:
        return CampaignBadge.PUBLISHED

    if status is CampaignStatus.ARCHIVED:
        return CampaignBadge.PUBLISHED if published_at else CampaignBadge.DRAFT

    return CampaignBadge.DRAFT


def resolve_publish_target(
    start_at: datetime | None, now: datetime | None = None
) -> CampaignStatus:
    """Publishing yields ACTIVE now, or SCHEDULED when the start is in the future."""
    moment = now or datetime.now(UTC)
    if start_at is None or start_at <= moment:
        return CampaignStatus.ACTIVE
    return CampaignStatus.SCHEDULED


def is_transition_allowed(current: CampaignStatus, target: CampaignStatus) -> bool:
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def is_viewable_by_recipient(effective_status: EffectiveStatus) -> bool:
    """Only a live campaign may be opened by a recipient."""
    return effective_status is EffectiveStatus.ACTIVE


# --- ads -------------------------------------------------------------------


def derive_ad_effective_status(
    *,
    status: AdStatus,
    is_complete: bool,
    campaign_effective: EffectiveStatus,
) -> AdEffectiveStatus:
    """What one ad is actually doing right now.

    An ad is delivering only when it is switched on, complete, **and** its
    campaign is live. CAMPAIGN_PAUSED is the case worth naming: the ad is
    faultless and still shows nothing, because the level above it is not
    running. Without it a user sees "ACTIVE" on an ad nobody can watch.
    """
    if status is AdStatus.ARCHIVED:
        return AdEffectiveStatus.ARCHIVED
    if status is AdStatus.DRAFT:
        return AdEffectiveStatus.DRAFT if is_complete else AdEffectiveStatus.INCOMPLETE
    if status is AdStatus.PAUSED:
        return AdEffectiveStatus.PAUSED

    # Switched on. Completeness first: it is the ad's own fault, and the more
    # actionable of the two reasons it might not be delivering.
    if not is_complete:
        return AdEffectiveStatus.INCOMPLETE
    if campaign_effective is not EffectiveStatus.ACTIVE:
        return AdEffectiveStatus.CAMPAIGN_PAUSED

    return AdEffectiveStatus.ACTIVE


def is_ad_transition_allowed(current: AdStatus, target: AdStatus) -> bool:
    if current == target:
        return True
    return target in ALLOWED_AD_TRANSITIONS.get(current, frozenset())


def is_ad_deliverable(effective_status: AdEffectiveStatus) -> bool:
    """Only a delivering ad may be opened by a recipient."""
    return effective_status is AdEffectiveStatus.ACTIVE
