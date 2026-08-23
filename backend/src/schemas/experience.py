"""Experience (creative) schemas."""

from pydantic import Field, field_validator, model_validator

from src.schemas.common import StrictModel
from src.schemas.option import OptionInput, OptionPublic, OptionRead
from src.schemas.validators import clean_text, validate_https_url, validate_video_url


class ExperienceInput(StrictModel):
    video_url: str | None = Field(None, max_length=2048)
    poster_url: str | None = Field(None, max_length=2048)
    captions_url: str | None = Field(None, max_length=2048)
    video_duration_seconds: int | None = Field(None, ge=0, le=86_400)
    headline: str | None = Field(None, max_length=80)
    personalised_message: str | None = Field(None, max_length=500)
    options: list[OptionInput] = Field(default_factory=list, max_length=2)

    @field_validator("headline", "personalised_message")
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
    def _positions_unique(self) -> "ExperienceInput":
        positions = [option.position for option in self.options]
        if len(positions) != len(set(positions)):
            raise ValueError("Each option must have a distinct position.")
        return self


class ExperienceRead(StrictModel):
    id: str
    video_url: str | None = None
    poster_url: str | None = None
    captions_url: str | None = None
    video_duration_seconds: int | None = None
    headline: str | None = None
    personalised_message: str | None = None
    options: list[OptionRead] = Field(default_factory=list)


class ExperiencePublic(StrictModel):
    """Recipient-facing creative, with variables already resolved."""

    id: str
    video_url: str
    poster_url: str | None = None
    captions_url: str | None = None
    headline: str | None = None
    personalised_message: str
    options: list[OptionPublic] = Field(default_factory=list)
