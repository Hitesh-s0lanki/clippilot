"""The campaign strategist's input brief and structured result.

These schemas are not only the wire contract - the result schema is handed to
the model as a tool definition, so every ``description=`` here is read by the
model as part of its instructions. They are written to be read that way.

The draft mirrors :class:`~src.schemas.campaign.CampaignCreate` field for
field and adds nothing. An agent that invented a field would produce a draft
the builder could not apply, so the constraints below - lengths, enums, two
options, the personalisation token - are the same ones the campaign schemas
enforce. Two blocks of ``CampaignCreate`` are deliberately absent:

``delivery``
    Pacing and send caps are operational settings whose defaults are already
    right. Research tells you nothing about them.
``ads[].status``
    A drafted ad is a draft. Switching it on is the user's decision, made after
    they have watched the video they still have to record.
``schedule.start_at`` / ``schedule.end_at``
    When a campaign runs is the user's decision, and the model has no clock.
    Only ``timezone`` is inferable, so only ``timezone`` is offered.
"""

from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from src.schemas.common import StrictModel
from src.schemas.enums import (
    BudgetType,
    CallToAction,
    CampaignObjective,
    FollowUpType,
    OptionIntent,
    SpecialCategory,
)
from src.schemas.validators import clean_text, validate_https_url


class Confidence(StrEnum):
    """How well evidence supports a suggestion."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# --- the brief the user submits --------------------------------------------


class CampaignBrief(StrictModel):
    """What the user tells the agent. Only ``requirements`` is mandatory."""

    requirements: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description=(
            "What the user wants, in their own words - and in practice the only field "
            "they fill in. Anything else useful (the company, its site, the market) is "
            "read out of this text or researched; the fields below are optional hints "
            "for programmatic callers, not questions to put to a person."
        ),
    )
    website_url: str | None = Field(
        None,
        max_length=2048,
        description="The business's own site. Researched first when present.",
    )
    competitor_urls: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Named competitors. When empty the agent finds its own.",
    )
    business_name: str | None = Field(None, max_length=120)
    industry: str | None = Field(None, max_length=120)
    audience_note: str | None = Field(
        None,
        max_length=500,
        description="Who the campaign is for, if the user already knows.",
    )
    objective: CampaignObjective | None = Field(
        None,
        description="Set when the user has already chosen. The agent must then keep it.",
    )
    market: str | None = Field(
        None,
        max_length=120,
        description="Country or region, e.g. 'India'. Drives currency, timezone and compliance.",
    )
    existing: "CampaignDraft | None" = Field(
        None,
        description=(
            "Fields the user has already filled in. The agent preserves every value "
            "present here and only drafts the gaps."
        ),
    )

    @field_validator("requirements", "business_name", "industry", "audience_note", "market")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("website_url")
    @classmethod
    def _site(cls, value: str | None) -> str | None:
        return validate_https_url(value, field="Website URL")

    @field_validator("competitor_urls")
    @classmethod
    def _competitors(cls, value: list[str]) -> list[str]:
        return [
            url for url in (validate_https_url(v, field="Competitor URL") for v in value) if url
        ]


# --- the draft the agent produces ------------------------------------------


class DraftOption(StrictModel):
    """One response button. A campaign has exactly two."""

    position: int = Field(..., ge=1, le=2, description="1 or 2. Each used exactly once.")
    label: str = Field(
        ...,
        min_length=1,
        max_length=40,
        description="Button text. Short and concrete: 'Tell me more', not 'Click here to learn'.",
    )
    intent: OptionIntent = Field(
        ...,
        description=(
            "POSITIVE for the option that advances the objective, NEGATIVE for the decline."
        ),
    )
    follow_up_type: FollowUpType = Field(
        FollowUpType.MESSAGE,
        description="MESSAGE shows text after the click. URL sends the recipient onward.",
    )
    follow_up_message: str | None = Field(
        None,
        max_length=500,
        description="Required when follow_up_type is MESSAGE. Must be empty when it is URL.",
    )
    follow_up_url: str | None = Field(
        None,
        max_length=2048,
        description=(
            "Required when follow_up_type is URL. Must be https and must be a page you "
            "actually saw during research - never a guessed path."
        ),
    )

    @field_validator("label", "follow_up_message")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("follow_up_url")
    @classmethod
    def _https(cls, value: str | None) -> str | None:
        return validate_https_url(value, field="Follow-up URL")

    @model_validator(mode="after")
    def _follow_up_matches_type(self) -> "DraftOption":
        if self.follow_up_type is FollowUpType.URL and self.follow_up_message:
            raise ValueError("follow_up_message must be empty when follow_up_type is URL.")
        if self.follow_up_type is FollowUpType.MESSAGE and self.follow_up_url:
            raise ValueError("follow_up_url must be empty when follow_up_type is MESSAGE.")
        return self


class DraftAd(StrictModel):
    """One ad. The video itself is the user's to supply.

    A campaign may hold several: draft more than one only when they are
    genuinely different angles worth testing against each other, not minor
    rewordings of the same idea.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Internal label, unique within the campaign. Name it after the angle.",
    )
    headline: str | None = Field(None, max_length=80, description="Optional. Above the video.")
    description: str | None = Field(
        None,
        max_length=500,
        description=(
            "Supporting line beneath the headline, read by the recipient. One sentence "
            "that earns the click the headline asked for. Leave null rather than padding."
        ),
    )
    cta: CallToAction = Field(
        CallToAction.LEARN_MORE,
        description=(
            "The action this ad asks for. It names the POSITIVE option's intent and "
            "supplies its default label, so pick the one that matches that button."
        ),
    )
    personalised_message: str | None = Field(
        None,
        max_length=500,
        description=(
            "The line the recipient reads. Use the literal token {{customer_name}} where "
            "their name belongs - the server substitutes it at delivery."
        ),
    )
    options: list[DraftOption] = Field(
        default_factory=list,
        max_length=2,
        description="Exactly two options: one POSITIVE, one NEGATIVE, positions 1 and 2.",
    )

    @field_validator("name", "headline", "description", "personalised_message")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @model_validator(mode="after")
    def _positions_unique(self) -> "DraftAd":
        positions = [option.position for option in self.options]
        if len(positions) != len(set(positions)):
            raise ValueError("Each option must have a distinct position.")
        return self


class DraftSchedule(StrictModel):
    """Only the part of the schedule that can be inferred."""

    timezone: str = Field(
        "UTC",
        max_length=64,
        description="IANA timezone for the business's market, e.g. 'Asia/Kolkata'.",
    )


class DraftBudget(StrictModel):
    """Money is always integer minor units plus an explicit currency."""

    budget_type: BudgetType = BudgetType.NONE
    budget_amount_minor: int | None = Field(
        None,
        ge=0,
        description="Minor units - paise, cents. 50000 means 500.00. Required unless type is NONE.",
    )
    currency: str = Field(
        "INR",
        min_length=3,
        max_length=3,
        description="ISO 4217 code matching the market, e.g. INR, USD, EUR.",
    )

    @field_validator("currency")
    @classmethod
    def _upper(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("currency must be a 3-letter ISO 4217 code.")
        return value.upper()

    @model_validator(mode="after")
    def _coherent(self) -> "DraftBudget":
        if self.budget_type is not BudgetType.NONE and self.budget_amount_minor is None:
            raise ValueError("budget_amount_minor is required unless budget_type is NONE.")
        return self


class DraftCompliance(StrictModel):
    """Regulated categories carry a mandatory disclaimer."""

    special_category: SpecialCategory = Field(
        SpecialCategory.NONE,
        description=(
            "FINANCIAL_PRODUCTS_SERVICES, CREDIT, EMPLOYMENT and HOUSING are regulated. "
            "Choose one whenever the offer plausibly falls under it."
        ),
    )
    disclaimer_text: str | None = Field(
        None,
        max_length=500,
        description="Required whenever special_category is not NONE.",
    )

    @field_validator("disclaimer_text")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @model_validator(mode="after")
    def _disclaimer_required(self) -> "DraftCompliance":
        if self.special_category is not SpecialCategory.NONE and not self.disclaimer_text:
            raise ValueError("disclaimer_text is required when special_category is not NONE.")
        return self


class DraftTracking(StrictModel):
    """UTM parameters appended to any follow-up URL."""

    utm_source: str | None = Field("trustvid", max_length=80)
    utm_medium: str | None = Field("interactive-video", max_length=80)
    utm_campaign: str | None = Field(
        None, max_length=80, description="Lowercase slug of the campaign name."
    )
    utm_content: str | None = Field(
        None, max_length=80, description="Lowercase slug of the creative angle."
    )


class CampaignDraft(StrictModel):
    """The campaign, as the builder form would be filled in.

    Every field maps one-to-one onto ``CampaignCreate``, so applying this draft
    to the form is assignment and not translation.
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=120,
        description="Internal name. Descriptive, not clever - the user has to find it later.",
    )
    description: str | None = Field(
        None, max_length=500, description="Internal note. Never shown to the recipient."
    )
    objective: CampaignObjective | None = Field(
        None,
        description=(
            "AWARENESS to be seen, ENGAGEMENT for any response, LEAD_CAPTURE for positive "
            "intent, CONVERSION to drive to a destination, RETENTION to re-engage."
        ),
    )
    schedule: DraftSchedule | None = None
    budget: DraftBudget | None = None
    compliance: DraftCompliance | None = None
    tracking: DraftTracking | None = None
    ads: list[DraftAd] = Field(
        default_factory=list,
        max_length=3,  # well inside MAX_ADS_PER_CAMPAIGN; see the field description
        description=(
            "The creatives. One is the normal answer. Draft a second or third only "
            "when the research supports genuinely distinct angles worth testing."
        ),
    )

    @field_validator("name", "description")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


# --- the research behind it -------------------------------------------------


class ResearchSource(StrictModel):
    """A page actually read. Never a URL that was merely plausible."""

    url: str = Field(..., max_length=2048)
    title: str | None = Field(None, max_length=200)
    used_for: str | None = Field(
        None, max_length=200, description="What this page contributed, in a few words."
    )


class BusinessProfile(StrictModel):
    """What the business is, as established from its own site."""

    name: str | None = Field(None, max_length=120)
    summary: str = Field(
        ..., max_length=600, description="What they sell and to whom, in two or three sentences."
    )
    industry: str | None = Field(None, max_length=120)
    value_propositions: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="Claims the business makes about itself, in its own words where possible.",
    )
    target_audience: str | None = Field(None, max_length=300)
    tone_of_voice: str | None = Field(
        None, max_length=200, description="How they write: formal, playful, technical, plain."
    )
    primary_call_to_action: str | None = Field(
        None, max_length=80, description="The action their own site pushes hardest."
    )


class CompetitorInsight(StrictModel):
    """One competitor, and what their advertising is doing."""

    name: str = Field(..., max_length=120)
    website_url: str | None = Field(None, max_length=2048)
    positioning: str | None = Field(None, max_length=400, description="The claim they compete on.")
    ad_angles: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Angles their marketing runs - the promise, not the format.",
    )
    hooks: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Actual headline or opening lines observed, quoted.",
    )
    gap: str | None = Field(
        None,
        max_length=400,
        description="What they are NOT saying. This is where the recommendation comes from.",
    )


class CreativeDirection(StrictModel):
    """The recommended angle, and why it is not what everyone else is running."""

    angle: str = Field(..., max_length=300, description="The one idea this campaign is built on.")
    why_it_wins: str = Field(
        ...,
        max_length=600,
        description="What it does that the competitor set does not. Cite the gap it exploits.",
    )
    video_concept: str = Field(
        ...,
        max_length=800,
        description="What the 15-30s video shows, beat by beat. Shootable, not abstract.",
    )
    opening_hook: str | None = Field(
        None, max_length=200, description="The first line of the video."
    )
    proof_points: list[str] = Field(
        default_factory=list, max_length=5, description="Facts that make the angle credible."
    )
    avoid: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Claims to stay away from - crowded, unsupported, or a compliance risk.",
    )


class FieldRationale(StrictModel):
    """Why one drafted field says what it says."""

    field: str = Field(
        ...,
        max_length=80,
        description="Dotted path into the draft, e.g. 'ads.0.options.0.label'.",
    )
    reason: str = Field(..., max_length=400)
    confidence: Confidence = Field(
        ...,
        description=(
            "HIGH when read directly from a source, MEDIUM when inferred from evidence, "
            "LOW when it is a reasonable guess the user should review."
        ),
    )


class CampaignStrategy(StrictModel):
    """The finished analysis and the campaign it recommends.

    Call this tool once, at the end, with everything filled in. Do not call it
    to report progress and do not call it twice.
    """

    researched: bool = Field(
        ...,
        description=(
            "True only if you actually read at least one page. False when you worked from "
            "the brief alone - say so rather than implying research that did not happen."
        ),
    )
    business: BusinessProfile
    competitors: list[CompetitorInsight] = Field(
        default_factory=list,
        max_length=5,
        description="Empty is honest when nothing could be verified. Invented entries are not.",
    )
    creative: CreativeDirection
    campaign: CampaignDraft = Field(
        ..., description="The draft the builder form is filled in from."
    )
    rationale: list[FieldRationale] = Field(
        default_factory=list,
        max_length=20,
        description="One entry per field the user is most likely to challenge.",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        max_length=6,
        description=(
            "What you could not determine and the user must decide - the video itself, "
            "the schedule, anything a source contradicted."
        ),
    )
    sources: list[ResearchSource] = Field(
        default_factory=list, max_length=20, description="Only pages you actually read."
    )


CampaignBrief.model_rebuild()
