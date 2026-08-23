"""UTM helpers."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from src.schemas.validators import slugify


def default_utm_campaign(name: str) -> str:
    """Slug of the campaign name, used when the user sets no utm_campaign."""
    return slugify(name, max_length=80)


def append_utm_params(url: str, params: dict[str, str | None]) -> str:
    """Append non-empty UTM params to a destination URL.

    Params already present on the destination win: ClipPilot never overwrites a
    value the user put there explicitly.
    """
    parsed = urlparse(url)
    existing = dict(parse_qsl(parsed.query, keep_blank_values=True))

    for key, value in params.items():
        if value and key not in existing:
            existing[key] = value

    return urlunparse(parsed._replace(query=urlencode(existing)))
