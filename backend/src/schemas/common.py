"""Shared value objects used inside the campaign wire format.

Grouping schedule / budget / delivery / compliance / tracking into nested
objects keeps the campaign payload navigable and lets the builder form map one
section to one object.
"""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.schemas.enums import BudgetType, PacingType, SpecialCategory
from src.schemas.validators import clean_text, validate_https_url


class StrictModel(BaseModel):
    """Rejects unknown keys so a typo in a payload is an error, not a silent no-op."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Schedule(StrictModel):
    start_at: datetime | None = Field(
        None, description="Null means the campaign is live as soon as it is published."
    )
    end_at: datetime | None = Field(None, description="Null means it runs until manually paused.")
    timezone: str = Field(
        "UTC",
        max_length=64,
        description="IANA timezone. Display preference only; storage is always UTC.",
    )

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"'{value}' is not a known IANA timezone.") from exc
        return value

    @model_validator(mode="after")
    def _end_after_start(self) -> "Schedule":
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at.")
        return self


class Budget(StrictModel):
    """Money is always integer minor units plus an explicit currency."""

    budget_type: BudgetType = BudgetType.NONE
    budget_amount_minor: int | None = Field(
        None, ge=0, description="Minor units (paise, cents). Never a float."
    )
    currency: str = Field("INR", min_length=3, max_length=3)
    spend_cap_minor: int | None = Field(None, ge=0)

    @field_validator("currency")
    @classmethod
    def _upper(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("currency must be a 3-letter ISO 4217 code.")
        return value.upper()

    @model_validator(mode="after")
    def _coherent(self) -> "Budget":
        if self.budget_type is not BudgetType.NONE and self.budget_amount_minor is None:
            raise ValueError("budget_amount_minor is required unless budget_type is NONE.")
        if (
            self.spend_cap_minor is not None
            and self.budget_amount_minor is not None
            and self.spend_cap_minor < self.budget_amount_minor
        ):
            raise ValueError("spend_cap_minor must be at least budget_amount_minor.")
        return self


class Delivery(StrictModel):
    pacing: PacingType = PacingType.STANDARD
    send_cap_total: int | None = Field(None, ge=1)
    send_cap_per_day: int | None = Field(None, ge=1)
    frequency_cap_per_recipient: int = Field(1, ge=1)

    @model_validator(mode="after")
    def _caps_coherent(self) -> "Delivery":
        if (
            self.send_cap_total is not None
            and self.send_cap_per_day is not None
            and self.send_cap_per_day > self.send_cap_total
        ):
            raise ValueError("send_cap_per_day cannot exceed send_cap_total.")
        return self


class Compliance(StrictModel):
    special_category: SpecialCategory = SpecialCategory.NONE
    disclaimer_text: str | None = Field(None, max_length=500)

    @field_validator("disclaimer_text")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)

    @model_validator(mode="after")
    def _disclaimer_required(self) -> "Compliance":
        if self.special_category is not SpecialCategory.NONE and not self.disclaimer_text:
            raise ValueError("disclaimer_text is required when special_category is not NONE.")
        return self


class Tracking(StrictModel):
    utm_source: str | None = Field("trustvid", max_length=80)
    utm_medium: str | None = Field("interactive-video", max_length=80)
    utm_campaign: str | None = Field(None, max_length=80)
    utm_content: str | None = Field(None, max_length=80)
    external_ref: str | None = Field(None, max_length=120)


class PrimaryMetric(StrictModel):
    """The single headline metric, chosen by the campaign objective."""

    key: str
    label: str
    value: float


class CampaignMetrics(StrictModel):
    """Read-only rollup shown on the dashboard card. Ignored on write."""

    views: int = 0
    interactions: int = 0
    interaction_rate: float = 0.0
    primary_metric: PrimaryMetric | None = None
    last_activity_at: datetime | None = None


__all__ = [
    "Budget",
    "CampaignMetrics",
    "Compliance",
    "Delivery",
    "PrimaryMetric",
    "Schedule",
    "StrictModel",
    "Tracking",
    "validate_https_url",
]
