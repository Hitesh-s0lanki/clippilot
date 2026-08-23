"""Campaign request and response schemas.

Write schemas carry only what the user controls. Everything derived -
``effective_status``, ``badge``, ``metrics`` - is read-only and ignored on
write, so a client echoing back a GET payload cannot corrupt server state.
"""

from datetime import datetime

from pydantic import Field, field_validator

from src.schemas.ad import MAX_ADS_PER_CAMPAIGN, AdInput, AdRead
from src.schemas.audience import AudienceSelection
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
    CampaignBadge,
    CampaignObjective,
    CampaignStatus,
    EffectiveStatus,
)
from src.schemas.validators import clean_text


class CampaignCreate(StrictModel):
    """Everything needed to save a draft. Only ``name`` is mandatory."""

    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    objective: CampaignObjective = CampaignObjective.ENGAGEMENT
    audience_id: str | None = Field(
        None,
        description=(
            "The audience this campaign targets. Optional on a draft, required "
            "to publish. Audiences are created and populated on /audiences."
        ),
    )

    schedule: Schedule = Field(default_factory=Schedule)
    budget: Budget = Field(default_factory=Budget)
    delivery: Delivery = Field(default_factory=Delivery)
    compliance: Compliance = Field(default_factory=Compliance)
    tracking: Tracking = Field(default_factory=Tracking)

    ads: list[AdInput] = Field(
        default_factory=list,
        max_length=MAX_ADS_PER_CAMPAIGN,
        description=(
            "Ads to create alongside the campaign. Optional: the builder creates the "
            "campaign first and adds creatives on its own screen. Names are unique within it."
        ),
    )

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
    audience_id: str | None = Field(
        None, description="Point the campaign at a different audience, or null to clear it."
    )

    schedule: Schedule | None = None
    budget: Budget | None = None
    delivery: Delivery | None = None
    compliance: Compliance | None = None
    tracking: Tracking | None = None

    # `ads` is absent on purpose. Once a campaign owns several of them,
    # replacing the whole list by index on every campaign PATCH is a footgun -
    # ads are created, edited and paused through /campaigns/{id}/ads. People
    # are absent for the same reason: an audience is a shared list edited on
    # /audiences, not a column of this campaign.

    @field_validator("name", "description")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


class StatusChange(StrictModel):
    """Body for the status transition endpoint."""

    status: CampaignStatus


class CampaignListItem(StrictModel):
    """Dashboard row. Omits ads, description and the audience breakdown."""

    id: str
    name: str
    objective: CampaignObjective
    status: CampaignStatus
    effective_status: EffectiveStatus
    badge: CampaignBadge
    poster_url: str | None = Field(None, description="Poster of the campaign's primary ad.")
    ad_count: int = 0
    live_ad_count: int = Field(0, description="Ads that are switched on and complete.")
    audience_name: str | None = Field(None, description="Null until an audience is selected.")
    audience_size: int = Field(0, description="People in the selected audience.")
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
    audience: AudienceSelection | None = Field(
        None, description="The list this campaign targets. Null until one is selected."
    )
    ads: list[AdRead] = Field(default_factory=list)
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
