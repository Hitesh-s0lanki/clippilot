"""Recipient-facing preview payloads.

These are the only schemas served without a Clerk session, so each is built
from an explicit allow-list: nothing internal (owner, budget, delivery caps,
the rest of the audience, follow-up copy) appears here.
"""

from datetime import datetime

from pydantic import Field

from src.schemas.ad import AdPublic
from src.schemas.common import StrictModel


class PreviewCompliance(StrictModel):
    special_category: str
    disclaimer_text: str | None = None


class CampaignPreview(StrictModel):
    campaign_id: str
    campaign_name: str
    customer_name: str
    member_id: str | None = Field(
        None, description="Who the copy was resolved for. Null for anonymous traffic."
    )
    ad: AdPublic
    compliance: PreviewCompliance

    # Variables that could not be resolved, surfaced so the builder can warn.
    # Never blanked silently and never a 500.
    unresolved_variables: list[str] = Field(default_factory=list)


class PublicCampaignCard(StrictModel):
    """One live campaign as the public ads library shows it.

    A deliberately thinner allow-list than ``CampaignPreview``: this listing is
    open to anyone, so it carries nothing that identifies a person. The copy
    is resolved with **nobody** bound, which is what turns
    ``{{customer_name}}`` into the neutral fallback instead of a real customer's
    name.
    """

    campaign_id: str
    campaign_name: str
    ad_id: str = Field(description="The ad this card previews. Open it to see this creative.")
    ad_name: str
    objective: str
    headline: str | None = None
    preview_message: str
    poster_url: str | None = None
    video_duration_seconds: int | None = None
    special_category: str
    option_labels: list[str] = Field(default_factory=list)
    published_at: datetime | None = None


class PublicCampaignPage(StrictModel):
    """Paginated ads library listing."""

    items: list[PublicCampaignCard] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
