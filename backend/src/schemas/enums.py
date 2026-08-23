"""Enumerations shared by the ORM models and the wire schemas.

Values are SCREAMING_SNAKE_CASE on the wire; the frontend owns human labels.
They are persisted as constrained TEXT rather than native database enums, so
adding a value is a code change and not a migration.
"""

from enum import StrEnum


class CampaignObjective(StrEnum):
    AWARENESS = "AWARENESS"
    ENGAGEMENT = "ENGAGEMENT"
    LEAD_CAPTURE = "LEAD_CAPTURE"
    CONVERSION = "CONVERSION"
    RETENTION = "RETENTION"


class CampaignStatus(StrEnum):
    """What the user chose. Persisted."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class EffectiveStatus(StrEnum):
    """Derived by the server from status + schedule + completeness."""

    INCOMPLETE = "INCOMPLETE"
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CampaignBadge(StrEnum):
    """The two-value badge the brief mandates for the dashboard."""

    DRAFT = "Draft"
    PUBLISHED = "Published"


class AdStatus(StrEnum):
    """What the user chose for one ad. Persisted.

    An ad's status is independent of its campaign's: pausing a single ad stops
    that creative without touching the rest of the campaign.
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class AdEffectiveStatus(StrEnum):
    """Derived from the ad's own status, its completeness, and its campaign.

    ``CAMPAIGN_PAUSED`` is the value that makes the two-level hierarchy legible:
    the ad is switched on and complete, and it still is not delivering, because
    the campaign above it is not live.
    """

    INCOMPLETE = "INCOMPLETE"
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"


class CallToAction(StrEnum):
    """The action an ad asks for.

    Names the intent of the POSITIVE response option rather than replacing it -
    the two-button interaction is unchanged. It supplies that button's default
    label, so a user who picks a CTA does not also have to write one.
    """

    LEARN_MORE = "LEARN_MORE"
    GET_QUOTE = "GET_QUOTE"
    BOOK_NOW = "BOOK_NOW"
    SIGN_UP = "SIGN_UP"
    CONTACT_US = "CONTACT_US"
    GET_OFFER = "GET_OFFER"
    SUBSCRIBE = "SUBSCRIBE"
    DOWNLOAD = "DOWNLOAD"
    APPLY_NOW = "APPLY_NOW"
    SHOP_NOW = "SHOP_NOW"


class BudgetType(StrEnum):
    NONE = "NONE"
    DAILY = "DAILY"
    LIFETIME = "LIFETIME"


class PacingType(StrEnum):
    STANDARD = "STANDARD"
    ACCELERATED = "ACCELERATED"


class SpecialCategory(StrEnum):
    NONE = "NONE"
    FINANCIAL_PRODUCTS_SERVICES = "FINANCIAL_PRODUCTS_SERVICES"
    CREDIT = "CREDIT"
    EMPLOYMENT = "EMPLOYMENT"
    HOUSING = "HOUSING"


class AudienceType(StrEnum):
    SINGLE = "SINGLE"
    LIST = "LIST"


class Gender(StrEnum):
    """Self-reported, and optional on every member.

    ``UNKNOWN`` is a real value rather than a null: a segment breakdown has to
    account for everyone, so "we were not told" is a bucket like any other.
    """

    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class AgeGroup(StrEnum):
    """Derived from ``age``. Never stored - a stored bucket goes stale on a birthday."""

    UNDER_18 = "UNDER_18"
    AGE_18_24 = "AGE_18_24"
    AGE_25_34 = "AGE_25_34"
    AGE_35_44 = "AGE_35_44"
    AGE_45_54 = "AGE_45_54"
    AGE_55_64 = "AGE_55_64"
    AGE_65_PLUS = "AGE_65_PLUS"
    UNKNOWN = "UNKNOWN"


class OptionIntent(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class FollowUpType(StrEnum):
    MESSAGE = "MESSAGE"
    URL = "URL"


class EventType(StrEnum):
    VIEW = "VIEW"
    RESPONSE = "RESPONSE"


# Statuses whose dashboard badge reads "Published".
PUBLISHED_STATUSES = frozenset(
    {
        CampaignStatus.SCHEDULED,
        CampaignStatus.ACTIVE,
        CampaignStatus.PAUSED,
        CampaignStatus.COMPLETED,
    }
)

# Statuses from which no further transition is allowed.
TERMINAL_STATUSES = frozenset({CampaignStatus.ARCHIVED})

# Which statuses a user may move one ad to. Mirrors ALLOWED_TRANSITIONS for
# campaigns, minus the schedule-driven states - an ad has no schedule of its
# own, it inherits its campaign's.
ALLOWED_AD_TRANSITIONS: dict[AdStatus, frozenset[AdStatus]] = {
    AdStatus.DRAFT: frozenset({AdStatus.ACTIVE, AdStatus.ARCHIVED}),
    AdStatus.ACTIVE: frozenset({AdStatus.PAUSED, AdStatus.DRAFT, AdStatus.ARCHIVED}),
    AdStatus.PAUSED: frozenset({AdStatus.ACTIVE, AdStatus.DRAFT, AdStatus.ARCHIVED}),
    AdStatus.ARCHIVED: frozenset(),
}

# The button label a CTA supplies when the user has not written one.
CTA_LABELS: dict[CallToAction, str] = {
    CallToAction.LEARN_MORE: "Learn more",
    CallToAction.GET_QUOTE: "Get a quote",
    CallToAction.BOOK_NOW: "Book now",
    CallToAction.SIGN_UP: "Sign up",
    CallToAction.CONTACT_US: "Contact us",
    CallToAction.GET_OFFER: "Get offer",
    CallToAction.SUBSCRIBE: "Subscribe",
    CallToAction.DOWNLOAD: "Download",
    CallToAction.APPLY_NOW: "Apply now",
    CallToAction.SHOP_NOW: "Shop now",
}

# Default disclaimer copy offered by the builder per special category.
DEFAULT_DISCLAIMERS: dict[SpecialCategory, str] = {
    SpecialCategory.FINANCIAL_PRODUCTS_SERVICES: (
        "Investments are subject to market risk. Read all scheme-related documents "
        "carefully. This is not investment advice."
    ),
}


# The age each bucket covers, inclusive of both bounds. ``None`` is open-ended.
# One definition, read by the Python resolver and by the SQL CASE that groups a
# segment breakdown - so the two can never disagree about who is 25-34.
AGE_GROUP_BOUNDS: dict[AgeGroup, tuple[int | None, int | None]] = {
    AgeGroup.UNDER_18: (None, 17),
    AgeGroup.AGE_18_24: (18, 24),
    AgeGroup.AGE_25_34: (25, 34),
    AgeGroup.AGE_35_44: (35, 44),
    AgeGroup.AGE_45_54: (45, 54),
    AgeGroup.AGE_55_64: (55, 64),
    AgeGroup.AGE_65_PLUS: (65, None),
}


def age_group_for(age: int | None) -> AgeGroup:
    """Bucket one age. An unknown age is its own group, never dropped."""
    if age is None:
        return AgeGroup.UNKNOWN

    for group, (low, high) in AGE_GROUP_BOUNDS.items():
        if (low is None or age >= low) and (high is None or age <= high):
            return group

    return AgeGroup.UNKNOWN
