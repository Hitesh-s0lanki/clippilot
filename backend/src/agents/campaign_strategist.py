"""The campaign strategist.

The builder form asks for a name, an objective, an audience type, a budget, a
compliance category, tracking parameters, a headline, a personalised message
and two response options with their follow-ups. Most users will not fill that
in from nothing. This agent turns a sentence of intent - plus, when there is
one, the business's own website - into a filled-in draft, with the competitor
research that justifies it.

It is also the reference implementation of :class:`~src.agents.base.BaseAgent`.
Everything below is declaration plus two small hooks; the loop, the tools, the
validation and the error mapping all live in the base class.
"""

from __future__ import annotations

from typing import ClassVar

from src.agents.base import BaseAgent
from src.agents.registry import register
from src.agents.toolkits import FIRECRAWL
from src.schemas.strategy import CampaignBrief, CampaignStrategy


@register
class CampaignStrategistAgent(BaseAgent[CampaignBrief, CampaignStrategy]):
    """Researches a business and its competitors, then drafts the campaign."""

    name: ClassVar[str] = "campaign-strategist"
    title: ClassVar[str] = "campaign strategist"
    description: ClassVar[str] = (
        "Reads the business's website and its competitors' advertising, then drafts a "
        "complete campaign - objective, compliance, copy and both response options."
    )

    prompt_file: ClassVar[str] = "campaign-strategist"
    input_model: ClassVar[type[CampaignBrief]] = CampaignBrief
    output_model: ClassVar[type[CampaignStrategy]] = CampaignStrategy

    toolsets: ClassVar[tuple[str, ...]] = (FIRECRAWL,)

    def prompt_variables(self, payload: CampaignBrief) -> dict[str, object]:
        """Values the prompt file needs that are not part of the user's turn."""
        return {
            "objective_locked": (
                f"The user has already chosen the objective: {payload.objective.value}. "
                "Keep it and build the campaign around it."
                if payload.objective
                else "The user has not chosen an objective. Choose the one the goal implies."
            ),
            "research_budget": (
                "Firecrawl is available. Read the business's own site first, then find and "
                "read competitors."
                if FIRECRAWL in self._toolkit.configured
                else "No research tools are available on this server. Work from the brief "
                "alone, set researched=false, and mark inferred fields LOW confidence."
            ),
        }

    def opening_message(self, payload: CampaignBrief) -> str:
        """The caller's brief, written out as the first user turn."""
        lines = [f"Requirements: {payload.requirements}"]

        for label, value in (
            ("Business", payload.business_name),
            ("Website", payload.website_url),
            ("Industry", payload.industry),
            ("Market", payload.market),
            ("Audience", payload.audience_note),
        ):
            if value:
                lines.append(f"{label}: {value}")

        if payload.competitor_urls:
            lines.append(f"Competitors to look at: {', '.join(payload.competitor_urls)}")

        if payload.existing:
            filled = payload.existing.model_dump(exclude_none=True, mode="json")
            if filled:
                lines.append(
                    "\nThe user has already filled these in. Keep every one of these values "
                    f"exactly as given and draft only what is missing:\n{filled}"
                )

        return "\n".join(lines)

    def finalise(self, output: CampaignStrategy, payload: CampaignBrief) -> CampaignStrategy:
        """Enforce in code the two rules that are expensive to lose in a prompt.

        A chosen objective is the user's decision, not the model's; and every
        ad's options must come back in a stable order, because the builder
        renders them by position and a swapped pair silently reverses the two
        buttons.
        """
        draft = output.campaign

        if payload.objective and draft.objective != payload.objective:
            draft = draft.model_copy(update={"objective": payload.objective})

        if any(len(ad.options) > 1 for ad in draft.ads):
            draft = draft.model_copy(
                update={
                    "ads": [
                        ad.model_copy(
                            update={"options": sorted(ad.options, key=lambda o: o.position)}
                        )
                        for ad in draft.ads
                    ]
                }
            )

        return output.model_copy(update={"campaign": draft})
