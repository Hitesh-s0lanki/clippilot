"""The publish contract.

A draft may be incomplete; publishing enforces the full contract. Returning a
structured list of blockers rather than raising lets the same function serve
two purposes: gating the publish call, and populating ``publish_blockers`` on
every read so the builder can disable the button and say precisely what is
missing.
"""

from dataclasses import dataclass

from src.schemas.enums import AdStatus, FollowUpType, SpecialCategory


@dataclass(frozen=True, slots=True)
class Blocker:
    """One unmet publish requirement."""

    field: str
    code: str
    message: str

    def as_detail(self) -> dict[str, str]:
        return {"field": self.field, "code": self.code, "message": self.message}


REQUIRED = "REQUIRED"
INCOMPLETE = "INCOMPLETE"
REQUIRED_WHEN = "REQUIRED_WHEN"
INVALID = "INVALID"


def collect_ad_blockers(ad, *, prefix: str = "") -> list[Blocker]:
    """Every reason one ad cannot be delivered, in form order.

    Used twice: to populate ``blockers`` on every ad read, and - with a
    ``prefix`` - to fold one ad's problems into the campaign's publish report.
    """
    blockers: list[Blocker] = []

    def field(name: str) -> str:
        return f"{prefix}{name}" if prefix else name

    if not ad.name:
        blockers.append(Blocker(field("name"), REQUIRED, "An ad name is required."))

    if not ad.video_url:
        blockers.append(
            Blocker(field("video_url"), REQUIRED, "A video URL is required before publishing.")
        )

    if not ad.personalised_message:
        blockers.append(
            Blocker(
                field("personalised_message"),
                REQUIRED,
                "A personalised message is required before publishing.",
            )
        )

    options = sorted(ad.options, key=lambda o: o.position)
    if len(options) != 2:
        blockers.append(
            Blocker(field("options"), REQUIRED, "Exactly two response options are required.")
        )
        return blockers

    for option in options:
        option_prefix = field(f"options.{option.position}")
        if not option.label:
            blockers.append(
                Blocker(f"{option_prefix}.label", REQUIRED, "A button label is required.")
            )
        if option.follow_up_type == FollowUpType.URL.value:
            if not option.follow_up_url:
                blockers.append(
                    Blocker(
                        f"{option_prefix}.follow_up_url",
                        REQUIRED_WHEN,
                        "A follow-up URL is required when the type is URL.",
                    )
                )
        elif not option.follow_up_message:
            blockers.append(
                Blocker(
                    f"{option_prefix}.follow_up_message",
                    REQUIRED_WHEN,
                    "A follow-up message is required when the type is MESSAGE.",
                )
            )

    return blockers


def collect_publish_blockers(campaign) -> list[Blocker]:
    """Every reason this campaign cannot be published, in form order.

    **At least one** non-archived ad must be complete - not all of them. That
    mirrors how a real ad account works: a half-written second creative sits in
    the campaign without blocking the first from running, and simply does not
    deliver until it is finished. When no ad is ready, the first unfinished
    ad's own blockers are folded in, so the report says which fields to fix
    rather than only that something is wrong.
    """
    blockers: list[Blocker] = []

    if not campaign.name:
        blockers.append(Blocker("name", REQUIRED, "A campaign name is required."))

    candidates = [ad for ad in campaign.ads if ad.status != AdStatus.ARCHIVED.value]

    if not candidates:
        blockers.append(Blocker("ads", REQUIRED, "At least one ad is required."))
    elif not any(ad.is_complete for ad in candidates):
        blockers.append(
            Blocker("ads", INCOMPLETE, "At least one ad must be complete before publishing.")
        )
        index = campaign.ads.index(candidates[0])
        blockers.extend(collect_ad_blockers(candidates[0], prefix=f"ads.{index}."))

    if campaign.audience_id is None or campaign.audience is None:
        blockers.append(
            Blocker("audience_id", REQUIRED, "An audience must be selected before publishing.")
        )
    elif campaign.audience.member_count == 0:
        blockers.append(
            Blocker(
                "audience_id",
                INCOMPLETE,
                f"'{campaign.audience.name}' has no people in it yet.",
            )
        )

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
