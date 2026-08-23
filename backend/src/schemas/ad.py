"""Ad (creative) schemas.

An ad is the creative a recipient watches. A campaign owns many, each with its
own status, so these carry a name and a lifecycle that the old single
"experience" did not need.

``*Public`` is the recipient-safe variant: it omits the ad's internal name, its
status and both follow-ups.
"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from src.schemas.common import StrictModel
from src.schemas.enums import AdEffectiveStatus, AdStatus, CallToAction
from src.schemas.option import OptionInput, OptionPublic, OptionRead
from src.schemas.validators import clean_text, validate_https_url, validate_video_url

# How many creatives one campaign may hold.
#
# Five, not twenty: a campaign is a single message tested a few ways, and a
# list long enough to need scrolling is a list nobody compares. The ceiling is
# a product decision, so it lives with the schema that expresses it rather than
# in the service that happens to enforce it.
MAX_ADS_PER_CAMPAIGN = 5


class AdInput(StrictModel):
    """Everything a user controls on one ad. Only ``name`` is mandatory."""

    name: str = Field(..., min_length=1, max_length=120, description="Internal label.")
    video_url: str | None = Field(None, max_length=2048)
    poster_url: str | None = Field(None, max_length=2048)
    captions_url: str | None = Field(None, max_length=2048)
    video_duration_seconds: int | None = Field(None, ge=0, le=86_400)

    headline: str | None = Field(None, max_length=80, description="Title above the video.")
    description: str | None = Field(
        None,
        max_length=500,
        description="Supporting line beneath the headline. Read by the recipient.",
    )
    personalised_message: str | None = Field(None, max_length=500)
    cta: CallToAction = Field(
        CallToAction.LEARN_MORE,
        description="Names the POSITIVE option's intent and supplies its default label.",
    )

    options: list[OptionInput] = Field(default_factory=list, max_length=2)

    @field_validator("name", "headline", "description", "personalised_message")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("video_url")
    @classmethod
    def _video(cls, value: str | None) -> str | None:
        return validate_video_url(value)

    @field_validator("poster_url", "captions_url")
    @classmethod
    def _https(cls, value: str | None) -> str | None:
        return validate_https_url(value, field="URL")

    @model_validator(mode="after")
    def _positions_unique(self) -> "AdInput":
        positions = [option.position for option in self.options]
        if len(positions) != len(set(positions)):
            raise ValueError("Each option must have a distinct position.")
        return self


class AdUpdate(StrictModel):
    """Partial update of one ad. Only supplied keys are applied.

    ``options`` replaces the whole set when present, so cross-option rules stay
    meaningful; ``status`` is not here - it moves through the status endpoint,
    which enforces the legal transitions.
    """

    name: str | None = Field(None, min_length=1, max_length=120)
    video_url: str | None = Field(None, max_length=2048)
    poster_url: str | None = Field(None, max_length=2048)
    captions_url: str | None = Field(None, max_length=2048)
    video_duration_seconds: int | None = Field(None, ge=0, le=86_400)

    headline: str | None = Field(None, max_length=80)
    description: str | None = Field(None, max_length=500)
    personalised_message: str | None = Field(None, max_length=500)
    cta: CallToAction | None = None

    options: list[OptionInput] | None = Field(None, max_length=2)

    @field_validator("name", "headline", "description", "personalised_message")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("video_url")
    @classmethod
    def _video(cls, value: str | None) -> str | None:
        return validate_video_url(value)

    @field_validator("poster_url", "captions_url")
    @classmethod
    def _https(cls, value: str | None) -> str | None:
        return validate_https_url(value, field="URL")

    @model_validator(mode="after")
    def _positions_unique(self) -> "AdUpdate":
        positions = [option.position for option in self.options or []]
        if len(positions) != len(set(positions)):
            raise ValueError("Each option must have a distinct position.")
        return self


class AdStatusChange(StrictModel):
    """Body for the ad status transition endpoint."""

    status: AdStatus


class AdRead(StrictModel):
    """One ad, as its owner sees it."""

    id: str
    campaign_id: str
    name: str

    status: AdStatus
    effective_status: AdEffectiveStatus = Field(
        AdEffectiveStatus.DRAFT,
        description="Derived from the ad's status, its completeness and its campaign's status.",
    )

    video_url: str | None = None
    poster_url: str | None = None
    captions_url: str | None = None
    video_duration_seconds: int | None = None

    headline: str | None = None
    description: str | None = None
    personalised_message: str | None = None
    cta: CallToAction = CallToAction.LEARN_MORE

    options: list[OptionRead] = Field(default_factory=list)

    # What this ad is still missing, so the builder can say so per ad rather
    # than only when the whole campaign fails to publish.
    blockers: list[str] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime


class AdPublic(StrictModel):
    """Recipient-facing creative, with variables already resolved."""

    id: str
    video_url: str
    poster_url: str | None = None
    captions_url: str | None = None
    headline: str | None = None
    description: str | None = None
    personalised_message: str
    cta: CallToAction = CallToAction.LEARN_MORE
    options: list[OptionPublic] = Field(default_factory=list)


class AdList(StrictModel):
    """Every ad on one campaign."""

    items: list[AdRead] = Field(default_factory=list)
    total: int = 0
