"""Recipient schemas."""

from pydantic import EmailStr, Field, field_validator

from src.schemas.common import StrictModel
from src.schemas.validators import clean_text


class RecipientInput(StrictModel):
    customer_name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20, pattern=r"^\+?[1-9]\d{6,19}$")
    external_ref: str | None = Field(None, max_length=120)
    attributes: dict[str, str] | None = None

    @field_validator("customer_name", "external_ref")
    @classmethod
    def _clean(cls, value: str | None) -> str | None:
        return clean_text(value)


class RecipientRead(StrictModel):
    id: str
    customer_name: str
    email: str | None = None
    phone: str | None = None
    external_ref: str | None = None


class Audience(StrictModel):
    audience_type: str
    recipient_count: int
    recipients: list[RecipientRead] = Field(default_factory=list)
