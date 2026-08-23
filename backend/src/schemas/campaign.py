"""Campaign request and response schemas.

Write schemas carry only what the user controls. Everything derived -
``effective_status``, ``badge``, ``metrics`` - is read-only and ignored on
write, so a client echoing back a GET payload cannot corrupt server state.
"""

from datetime import datetime

from pydantic import Field, field_validator

from src.schemas.common import (
    Budget,
    CampaignMetrics,
    Compliance,
    Delivery,
    Schedule,
    StrictModel,
    Tracking,
)
from src.schemas.enums import (
    AudienceType,
    CampaignBadge,
    CampaignObjective,
    CampaignStatus,
    EffectiveStatus,
)
from src.schemas.experience import ExperienceInput, ExperienceRead
from src.schemas.recipient import Audience, RecipientInput
from src.schemas.validators import clean_text


class CampaignCreate(StrictModel):
    """Everything needed to save a draft. Only ``name`` is mandatory."""

    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    objective: CampaignObjective = CampaignObjective.ENGAGEMENT
    audience_type: AudienceType = AudienceType.SINGLE

    schedule: Schedule = Field(default_factory=Schedule)
    budget: Budget = Field(default_factory=Budget)
    delivery: Delivery = Field(default_factory=Delivery)
    compliance: Compliance = Field(default_factory=Compliance)
    tracking: Tracking = Field(default_factory=Tracking)

    experience: ExperienceInput = Field(default_factory=ExperienceInput)
    recipients: list[RecipientInput] = Field(default_factory=list, max_length=1000)

    @field_validator("name", "description")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


class CampaignUpdate(StrictModel):
    """Partial update. Only supplied keys are applied.

    Nested blocks replace wholesale rather than merging field-by-field, which
    keeps cross-field validation (``end_at > start_at``) meaningful.
    """

    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    objective: CampaignObjective | None = None
    audience_type: AudienceType | None = None

    schedule: Schedule | None = None
    budget: Budget | None = None
    delivery: Delivery | None = None
    compliance: Compliance | None = None
    tracking: Tracking | None = None

    experience: ExperienceInput | None = None
    recipients: list[RecipientInput] | None = Field(None, max_length=1000)

    @field_validator("name", "description")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


class StatusChange(StrictModel):
    """Body for the status transition endpoint."""

    status: CampaignStatus


class CampaignListItem(StrictModel):
    """Dashboard row. Omits recipients, options and description."""

    id: str
    name: str
    objective: CampaignObjective
    status: CampaignStatus
    effective_status: EffectiveStatus
    badge: CampaignBadge
    poster_url: str | None = None
    recipient_count: int = 0
    metrics: CampaignMetrics = Field(default_factory=CampaignMetrics)
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None


class CampaignRead(StrictModel):
    """Full campaign read."""

    id: str
    name: str
    description: str | None = None
    objective: CampaignObjective

    status: CampaignStatus
    effective_status: EffectiveStatus
    badge: CampaignBadge

    schedule: Schedule
    budget: Budget
    delivery: Delivery
    compliance: Compliance
    tracking: Tracking
    audience: Audience
    experience: ExperienceRead | None = None
    metrics: CampaignMetrics = Field(default_factory=CampaignMetrics)

    # Publish-readiness, so the builder can disable the Publish button and show
    # exactly what is missing without attempting the call.
    publish_blockers: list[str] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    archived_at: datetime | None = None


class CampaignPage(StrictModel):
    """Paginated dashboard listing."""

    items: list[CampaignListItem]
    total: int
    limit: int
    offset: int
