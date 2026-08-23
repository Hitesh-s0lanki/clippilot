"""Audience request and response schemas.

Only ``full_name`` is ever required of a member. Everything else is optional
because a real uploaded list is ragged, and a list that refuses a row for a
missing phone number is a list nobody can upload.
"""

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from src.schemas.common import StrictModel
from src.schemas.enums import AgeGroup, Gender
from src.schemas.validators import clean_text, normalise_place

# A phone as E.164 without separators. Matches what the importer normalises to.
PHONE_PATTERN = r"^\+?[1-9]\d{6,19}$"

# How many members one write may carry. A bigger file is imported in batches.
MAX_MEMBERS_PER_WRITE = 1000


class AudienceMemberInput(StrictModel):
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="The only required field. Resolves {{customer_name}} in campaign copy.",
    )
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20, pattern=PHONE_PATTERN)
    age: int | None = Field(
        None,
        ge=13,
        le=120,
        description="The age itself, not a bracket. Brackets are derived at read time.",
    )
    gender: Gender = Gender.UNKNOWN
    city: str | None = Field(None, max_length=80)
    country: str | None = Field(None, max_length=56)
    external_ref: str | None = Field(None, max_length=120, description="CRM contact id.")
    attributes: dict[str, str] | None = Field(
        None, description="Free-form extras carried through import and export untouched."
    )

    @field_validator("full_name", "external_ref")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("city", "country")
    @classmethod
    def _place(cls, value: str | None) -> str | None:
        return normalise_place(value)


class AudienceMemberRead(StrictModel):
    id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    age: int | None = None
    age_group: AgeGroup = Field(
        AgeGroup.UNKNOWN, description="Derived from age. Never stored, so it cannot go stale."
    )
    gender: Gender = Gender.UNKNOWN
    city: str | None = None
    country: str | None = None
    external_ref: str | None = None
    attributes: dict[str, str] | None = None
    created_at: datetime


class AudienceMemberPage(StrictModel):
    """One filtered page of people, plus how many matched the filter."""

    items: list[AudienceMemberRead]
    total: int
    limit: int
    offset: int


class SegmentBucket(StrictModel):
    """One slice of a breakdown.

    ``key`` is an enum value for age and gender and the stored text for a city
    or a country. The frontend owns the human label either way.
    """

    key: str
    count: int
    share: float = Field(..., description="Fraction of the whole audience, 0-1, rounded to 4dp.")


class AudienceSegments(StrictModel):
    """What the audience is made of, without naming anybody.

    This is the screen's headline. A list of 100 names tells you nothing; the
    same 100 people broken down by age, gender and place is what you choose a
    campaign's targeting from.
    """

    total: int
    with_email: int = Field(..., description="Members reachable by email.")
    with_phone: int = Field(..., description="Members reachable by phone.")
    age_groups: list[SegmentBucket] = Field(default_factory=list)
    genders: list[SegmentBucket] = Field(default_factory=list)
    cities: list[SegmentBucket] = Field(default_factory=list)
    countries: list[SegmentBucket] = Field(default_factory=list)


class AudienceCreate(StrictModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)
    members: list[AudienceMemberInput] = Field(
        default_factory=list, max_length=MAX_MEMBERS_PER_WRITE
    )

    @field_validator("name", "description")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


class AudienceUpdate(StrictModel):
    """Renames and re-describes. Membership is managed on its own routes."""

    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=500)

    @field_validator("name", "description")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


class AudienceMembersInput(StrictModel):
    """Body for a bulk add. One CSV upload is one call."""

    members: list[AudienceMemberInput] = Field(..., min_length=1, max_length=MAX_MEMBERS_PER_WRITE)


class SkippedMember(StrictModel):
    """One row that did not land, and why."""

    index: int = Field(..., description="Position in the submitted list, 0-based.")
    full_name: str
    reason: str


class AudienceImportResult(StrictModel):
    """The outcome of a bulk add.

    A partial success is the normal case, not an error: one repeated email in a
    200-row file should cost that row, not the file. Every skipped row is named
    so the user can see what did not land instead of silently losing it.
    """

    added: int
    skipped: list[SkippedMember] = Field(default_factory=list)
    member_count: int = Field(..., description="Size of the audience after the import.")


class AudienceListItem(StrictModel):
    id: str
    name: str
    description: str | None = None
    member_count: int = 0
    campaign_count: int = Field(0, description="Campaigns currently pointing at this audience.")
    created_at: datetime
    updated_at: datetime


class AudienceRead(AudienceListItem):
    """One audience with its breakdown. Members come from the members route."""

    segments: AudienceSegments


class AudiencePage(StrictModel):
    items: list[AudienceListItem]
    total: int
    limit: int
    offset: int


class AudienceSelection(StrictModel):
    """What a campaign says about the list it targets."""

    id: str
    name: str
    member_count: int
