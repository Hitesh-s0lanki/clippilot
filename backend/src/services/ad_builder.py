"""Applying an ad payload to an ad row.

Shared by the campaign service (which creates ads inline with a campaign) and
the ad service (which owns them thereafter), so the option-reconciliation rules
are written once.
"""

from __future__ import annotations

from src.app.errors import ApiError
from src.models import Ad, AdOption
from src.schemas.ad import AdInput, AdUpdate
from src.schemas.enums import CTA_LABELS, CallToAction, OptionIntent
from src.schemas.option import OptionInput


def guard_unique_ad_names(names: list[str]) -> None:
    """Reject duplicate ad names before the unique index does, case-insensitively."""
    seen: set[str] = set()
    for name in names:
        lowered = (name or "").lower()
        if lowered in seen:
            raise ApiError(
                409,
                "AD_NAME_TAKEN",
                f"This campaign already has an ad named '{name}'.",
                details=[
                    {
                        "field": "name",
                        "code": "DUPLICATE",
                        "message": "Ad names must be unique within a campaign.",
                    }
                ],
            )
        seen.add(lowered)


def default_option_label(position: int, intent: OptionIntent, cta: CallToAction) -> str:
    """The label to use when the user has not written one.

    This is what the CTA buys: choosing BOOK_NOW writes "Book now" onto the
    positive button, so picking a call to action is not also a copywriting
    task. The negative button gets a neutral decline rather than a CTA.
    """
    if intent is OptionIntent.POSITIVE:
        return CTA_LABELS.get(cta, CTA_LABELS[CallToAction.LEARN_MORE])
    if intent is OptionIntent.NEGATIVE:
        return "Not right now"
    return f"Option {position}"


def apply_ad_input(ad: Ad, payload: AdInput) -> Ad:
    """Write a full ad payload onto an ad row."""
    ad.name = payload.name
    ad.video_url = payload.video_url
    ad.poster_url = payload.poster_url
    ad.captions_url = payload.captions_url
    ad.video_duration_seconds = payload.video_duration_seconds
    ad.headline = payload.headline
    ad.description = payload.description
    ad.personalised_message = payload.personalised_message
    ad.cta = payload.cta.value

    _reconcile_options(ad, payload.options, payload.cta)
    return ad


def apply_ad_update(ad: Ad, payload: AdUpdate) -> Ad:
    """Write a partial ad payload onto an ad row. Only supplied keys apply."""
    supplied = payload.model_dump(exclude_unset=True)

    for field in (
        "name",
        "video_url",
        "poster_url",
        "captions_url",
        "video_duration_seconds",
        "headline",
        "description",
        "personalised_message",
    ):
        if field in supplied:
            setattr(ad, field, getattr(payload, field))

    if "cta" in supplied and payload.cta is not None:
        ad.cta = payload.cta.value

    if payload.options is not None:
        _reconcile_options(ad, payload.options, CallToAction(ad.cta))

    return ad


def _reconcile_options(ad: Ad, options: list[OptionInput], cta: CallToAction) -> None:
    """Update options in place, matched by position.

    Options are reconciled rather than cleared and re-added. Delete-orphan plus
    a fresh insert makes SQLAlchemy emit the INSERT before the DELETE in one
    flush, which trips uniq_option_position. Updating in place also keeps each
    option's analytics key, so rewording a label does not split its metric into
    two series.
    """
    existing = {option.position: option for option in ad.options}
    incoming = {option.position: option for option in options}

    for position, option_input in sorted(incoming.items()):
        option = existing.get(position)
        if option is None:
            option = AdOption(position=position, key=option_input.derive_key())
            ad.options.append(option)

        option.label = option_input.label or default_option_label(
            position, option_input.intent, cta
        )
        option.intent = option_input.intent.value
        option.follow_up_type = option_input.follow_up_type.value
        option.follow_up_message = option_input.follow_up_message
        option.follow_up_url = option_input.follow_up_url

    for position, option in existing.items():
        if position not in incoming:
            ad.options.remove(option)
