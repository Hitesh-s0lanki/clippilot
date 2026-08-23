"""Response option schemas."""

from pydantic import Field, field_validator, model_validator

from src.schemas.common import StrictModel
from src.schemas.enums import FollowUpType, OptionIntent
from src.schemas.validators import clean_text, slugify, validate_https_url


class OptionInput(StrictModel):
    """One response button as submitted by the builder."""

    position: int = Field(..., ge=1, le=2, description="1 or 2. Unique per experience.")
    label: str | None = Field(None, max_length=40, description="Button text.")
    intent: OptionIntent = OptionIntent.NEUTRAL
    follow_up_type: FollowUpType = FollowUpType.MESSAGE
    follow_up_message: str | None = Field(None, max_length=500)
    follow_up_url: str | None = Field(None, max_length=2048)

    @field_validator("label", "follow_up_message")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("follow_up_url")
    @classmethod
    def _https_only(cls, value: str | None) -> str | None:
        return validate_https_url(value, field="Follow-up URL")

    @model_validator(mode="after")
    def _follow_up_matches_type(self) -> "OptionInput":
        # Drafts may be incomplete, so a missing follow-up is allowed here and
        # enforced by the publish contract instead. What is rejected is a
        # follow-up that contradicts its declared type.
        if self.follow_up_type is FollowUpType.URL and self.follow_up_message:
            raise ValueError("follow_up_message must be empty when follow_up_type is URL.")
        if self.follow_up_type is FollowUpType.MESSAGE and self.follow_up_url:
            raise ValueError("follow_up_url must be empty when follow_up_type is MESSAGE.")
        return self

    def derive_key(self) -> str:
        """Stable analytics key, slugged from the label at creation time."""
        return slugify(self.label) if self.label else f"option-{self.position}"


class OptionRead(StrictModel):
    id: str
    position: int
    key: str
    label: str
    intent: OptionIntent
    follow_up_type: FollowUpType
    follow_up_message: str | None = None
    follow_up_url: str | None = None


class OptionPublic(StrictModel):
    """What the recipient-facing preview page may see.

    Deliberately omits the follow-up: revealing both outcomes before the click
    would let a recipient read the response they did not choose.
    """

    id: str
    position: int
    key: str
    label: str
