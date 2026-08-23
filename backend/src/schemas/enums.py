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

# Default disclaimer copy offered by the builder per special category.
DEFAULT_DISCLAIMERS: dict[SpecialCategory, str] = {
    SpecialCategory.FINANCIAL_PRODUCTS_SERVICES: (
        "Investments are subject to market risk. Read all scheme-related documents "
        "carefully. This is not investment advice."
    ),
}
