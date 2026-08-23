"""Recipient-facing preview payload.

This is the only schema served without a Clerk session, so it is built from an
explicit allow-list: nothing internal (owner, budget, delivery caps, other
recipients, follow-up copy) appears here.
"""

from pydantic import Field

from src.schemas.common import StrictModel
from src.schemas.experience import ExperiencePublic


class PreviewCompliance(StrictModel):
    special_category: str
    disclaimer_text: str | None = None


class CampaignPreview(StrictModel):
    campaign_id: str
    campaign_name: str
    customer_name: str
    recipient_id: str | None = None
    experience: ExperiencePublic
    compliance: PreviewCompliance

    # Variables that could not be resolved, surfaced so the builder can warn.
    # Never blanked silently and never a 500.
    unresolved_variables: list[str] = Field(default_factory=list)
