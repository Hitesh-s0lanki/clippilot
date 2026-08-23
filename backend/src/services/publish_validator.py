"""The publish contract.

A draft may be incomplete; publishing enforces the full contract. Returning a
structured list of blockers rather than raising lets the same function serve
two purposes: gating the publish call, and populating ``publish_blockers`` on
every read so the builder can disable the button and say precisely what is
missing.
"""

from dataclasses import dataclass

from src.schemas.enums import FollowUpType, SpecialCategory


@dataclass(frozen=True, slots=True)
class Blocker:
    """One unmet publish requirement."""

    field: str
    code: str
    message: str

    def as_detail(self) -> dict[str, str]:
        return {"field": self.field, "code": self.code, "message": self.message}


REQUIRED = "REQUIRED"
REQUIRED_WHEN = "REQUIRED_WHEN"
INVALID = "INVALID"


def collect_publish_blockers(campaign) -> list[Blocker]:  # noqa: C901 - flat rule list
    """Every reason this campaign cannot be published, in form order."""
    blockers: list[Blocker] = []
    experience = campaign.experience

    if not campaign.name:
        blockers.append(Blocker("name", REQUIRED, "A campaign name is required."))

    if not experience or not experience.video_url:
        blockers.append(
            Blocker(
                "experience.video_url",
                REQUIRED,
                "A video URL is required before publishing.",
            )
        )

    if not experience or not experience.personalised_message:
        blockers.append(
            Blocker(
                "experience.personalised_message",
                REQUIRED,
                "A personalised message is required before publishing.",
            )
        )

    options = sorted(experience.options, key=lambda o: o.position) if experience else []

    if len(options) != 2:
        blockers.append(
            Blocker(
                "experience.options",
                REQUIRED,
                "Exactly two response options are required.",
            )
        )
    else:
        for option in options:
            prefix = f"experience.options.{option.position}"
            if not option.label:
                blockers.append(Blocker(f"{prefix}.label", REQUIRED, "A button label is required."))
            if option.follow_up_type == FollowUpType.URL.value:
                if not option.follow_up_url:
                    blockers.append(
                        Blocker(
                            f"{prefix}.follow_up_url",
                            REQUIRED_WHEN,
                            "A follow-up URL is required when the type is URL.",
                        )
                    )
            elif not option.follow_up_message:
                blockers.append(
                    Blocker(
                        f"{prefix}.follow_up_message",
                        REQUIRED_WHEN,
                        "A follow-up message is required when the type is MESSAGE.",
                    )
                )

    if not campaign.recipients:
        blockers.append(Blocker("recipients", REQUIRED, "At least one recipient is required."))

    if campaign.special_category != SpecialCategory.NONE.value and not campaign.disclaimer_text:
        blockers.append(
            Blocker(
                "compliance.disclaimer_text",
                REQUIRED_WHEN,
                "A disclaimer is required for this special category.",
            )
        )

    if campaign.budget_type != "NONE" and campaign.budget_amount_minor is None:
        blockers.append(
            Blocker(
                "budget.budget_amount_minor",
                REQUIRED_WHEN,
                "A budget amount is required when a budget type is set.",
            )
        )

    if campaign.pacing == "ACCELERATED" and campaign.end_at is None:
        blockers.append(
            Blocker(
                "delivery.pacing",
                INVALID,
                "Accelerated pacing requires an end date to accelerate through.",
            )
        )

    return blockers


def is_publishable(campaign) -> bool:
    return not collect_publish_blockers(campaign)
