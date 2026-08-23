"""Reusable field sanitisation and validation.

Storage keeps what the user typed; escaping happens at render time. What is
rejected here is input that is malformed, unsafe to fetch, or would corrupt
display (control characters).
"""

import ipaddress
import re
import unicodedata
from urllib.parse import urlparse

# Matches any C0/C1 control character except tab and newline.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
_WHITESPACE_RUN = re.compile(r"[ \t]{2,}")
_SLUG_STRIP = re.compile(r"[^a-z0-9]+")

ALLOWED_VIDEO_SUFFIXES = (".mp4", ".webm", ".mov")


def clean_text(value: str | None) -> str | None:
    """Trim, collapse internal whitespace runs and reject control characters."""
    if value is None:
        return None

    if _CONTROL_CHARS.search(value):
        raise ValueError("Text may not contain control characters.")

    collapsed = _WHITESPACE_RUN.sub(" ", value.strip())
    return collapsed or None


def require_text(value: str | None, *, field: str) -> str:
    cleaned = clean_text(value)
    if not cleaned:
        raise ValueError(f"{field} is required.")
    return cleaned


# Spellings people type for the same place, folded so a segment breakdown does
# not split "USA" and "United States" into two buckets. Deliberately short: the
# goal is to catch what a spreadsheet actually contains, not to be a gazetteer.
_PLACE_ALIASES: dict[str, str] = {
    "usa": "United States",
    "us": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "uae": "United Arab Emirates",
    "bombay": "Mumbai",
    "bengaluru": "Bangalore",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "new york city": "New York",
    "nyc": "New York",
}


def normalise_place(value: str | None) -> str | None:
    """Fold a city or country name to one spelling.

    Grouping is only as good as the strings it groups. Left alone, one upload
    saying "delhi" and another saying "Delhi" become two segments of the same
    city, and the breakdown quietly lies about reach.
    """
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    folded = _PLACE_ALIASES.get(cleaned.casefold())
    if folded is not None:
        return folded

    # Title-case only what was typed in one case throughout. "McKinsey" and
    # "Rio de Janeiro" are already spelled deliberately; lowering them would be
    # a downgrade.
    if cleaned.islower() or cleaned.isupper():
        return cleaned.title()

    return cleaned


def slugify(value: str, *, max_length: int = 60) -> str:
    """Produce a stable, URL-safe analytics key from a label."""
    normalised = unicodedata.normalize("NFKD", value)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii").lower()
    slug = _SLUG_STRIP.sub("-", ascii_only).strip("-")
    return (slug[:max_length].rstrip("-")) or "option"


def validate_https_url(value: str | None, *, field: str = "URL") -> str | None:
    """Accept only https URLs pointing at a public host.

    Blocking private and loopback addresses closes the obvious SSRF path: the
    preview page and any future server-side fetch will follow these URLs.
    """
    if value is None:
        return None

    cleaned = clean_text(value)
    if not cleaned:
        return None

    parsed = urlparse(cleaned)

    if parsed.scheme != "https":
        raise ValueError(f"{field} must use https.")
    if not parsed.hostname:
        raise ValueError(f"{field} is not a valid URL.")

    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise ValueError(f"{field} may not point at localhost.")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # A hostname rather than a literal address; DNS is not resolved here.
        return cleaned

    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
    ):
        raise ValueError(f"{field} may not point at a private address.")

    return cleaned


def validate_video_url(value: str | None) -> str | None:
    """An https URL whose path looks like a playable video file."""
    cleaned = validate_https_url(value, field="Video URL")
    if cleaned is None:
        return None

    path = urlparse(cleaned).path.lower()
    if not path.endswith(ALLOWED_VIDEO_SUFFIXES):
        allowed = ", ".join(ALLOWED_VIDEO_SUFFIXES)
        raise ValueError(f"Video URL must end in one of: {allowed}")

    return cleaned
