"""Analytics response schemas."""

from datetime import date, datetime

from pydantic import Field

from src.schemas.common import PrimaryMetric, StrictModel
from src.schemas.enums import OptionIntent


class OptionBreakdown(StrictModel):
    """Per-option click counts.

    A row is returned for every option, including zero-click ones - a chart
    with a missing bar is a bug the frontend should not have to guess around.
    """

    option_id: str
    position: int
    key: str
    label: str
    intent: OptionIntent
    clicks: int = 0
    share: float = Field(
        0.0, ge=0.0, le=1.0, description="Fraction of interactions. Sums to 1.0, or 0 when none."
    )


class TimeseriesPoint(StrictModel):
    date: date
    views: int = 0
    interactions: int = 0


class CampaignAnalytics(StrictModel):
    campaign_id: str
    objective: str

    views: int = 0
    interactions: int = 0
    interaction_rate: float = Field(
        0.0, ge=0.0, description="interactions / views. 0 when views is 0 - never divides by zero."
    )
    unique_viewers: int = 0

    by_option: list[OptionBreakdown] = Field(default_factory=list)
    primary_metric: PrimaryMetric | None = None

    first_activity_at: datetime | None = None
    last_activity_at: datetime | None = None
    timeseries: list[TimeseriesPoint] = Field(default_factory=list)
