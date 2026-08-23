"""Event schemas for the recipient-facing preview page."""

from datetime import datetime

from pydantic import Field, field_validator

from src.schemas.common import StrictModel
from src.schemas.enums import EventType


class ViewEventCreate(StrictModel):
    session_id: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Client-generated, stable for one preview session. The dedup key.",
    )
    ad_id: str | None = Field(
        None,
        description=(
            "Which ad was on screen. Optional: without it the campaign's "
            "primary ad is assumed, and on a response the option id already "
            "identifies its ad."
        ),
    )
    member_id: str | None = Field(
        None,
        description=(
            "Which member of the campaign's audience opened it. Optional: a "
            "shared link carries nobody, and the event is recorded anonymously."
        ),
    )

    @field_validator("session_id")
    @classmethod
    def _safe(cls, value: str) -> str:
        if not value.replace("-", "").replace("_", "").isalnum():
            raise ValueError("session_id must be alphanumeric, dashes or underscores.")
        return value


class ResponseEventCreate(ViewEventCreate):
    option_id: str = Field(..., description="Must belong to this campaign.")


class EventRead(StrictModel):
    id: str
    type: EventType
    session_id: str
    ad_id: str | None = None
    option_id: str | None = None
    occurred_at: datetime

    # True when this session had already recorded the event. The original is
    # returned with 200 rather than a 409: a double-click is not a client error
    # and the preview must not show a failure state for one.
    deduplicated: bool = False


class ResponseResult(StrictModel):
    """What the preview page renders after a response is recorded."""

    event: EventRead
    follow_up_type: str
    follow_up_message: str | None = None
    follow_up_url: str | None = None
