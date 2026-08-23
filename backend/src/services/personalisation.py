"""Variable substitution for personalised copy.

The brief mandates ``{{customer_name}}``, which stays the spelling of the tag
even though the field behind it is now ``audience_member.full_name``. The
resolver is generalised so the same substitution runs over the headline, the
personalised message and the follow-up copy, and so the segmentation fields an
audience carries can be addressed too.

Resolution rules:

- Unknown variable -> left literal and reported, never blanked, never a 500.
- Missing member value -> falls back to a neutral word, so a preview never
  renders a gap where a value should be.
- Whitespace inside the braces is tolerated: ``{{ customer_name }}`` resolves.
- Escaping is a render-time concern; storage keeps what the user typed.
"""

import re
from dataclasses import dataclass, field

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

MISSING_NAME_FALLBACK = "there"

# A place has no neutral word the way a name has "there", but it needs one all
# the same: rendering "" turns "an opportunity in {{city}}" into "an
# opportunity in ." for every member whose city was never filled in - and a
# ragged list is the normal case, so that is not an edge.
MISSING_CITY_FALLBACK = "your city"
MISSING_COUNTRY_FALLBACK = "your country"

KNOWN_VARIABLES = frozenset(
    {"customer_name", "first_name", "city", "country", "campaign_name", "option_label"}
)


@dataclass(slots=True)
class PersonalisationContext:
    """Values available to the resolver for one render.

    ``customer_name`` is the brief's tag and keeps its name on the wire; the
    value behind it is the audience member's full name. ``city`` and
    ``country`` come from the same member, so copy can address the segment the
    list was chosen for.
    """

    customer_name: str | None = None
    campaign_name: str | None = None
    option_label: str | None = None
    city: str | None = None
    country: str | None = None

    @property
    def first_name(self) -> str | None:
        """The leading word of the full name.

        "Hi Rahul" reads like a person wrote it and "Hi Rahul Mehta" does not,
        which is the whole reason a campaign personalises at all.
        """
        if not self.customer_name:
            return None
        return self.customer_name.split()[0]

    def as_mapping(self) -> dict[str, str]:
        return {
            "customer_name": self.customer_name or MISSING_NAME_FALLBACK,
            "first_name": self.first_name or MISSING_NAME_FALLBACK,
            "campaign_name": self.campaign_name or "",
            "option_label": self.option_label or "",
            "city": self.city or MISSING_CITY_FALLBACK,
            "country": self.country or MISSING_COUNTRY_FALLBACK,
        }


@dataclass(slots=True)
class ResolvedText:
    text: str
    unresolved: list[str] = field(default_factory=list)


def resolve(template: str | None, context: PersonalisationContext) -> ResolvedText:
    """Substitute known variables, leaving unknown ones literal."""
    if not template:
        return ResolvedText(text="", unresolved=[])

    values = context.as_mapping()
    unresolved: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in KNOWN_VARIABLES:
            if name not in unresolved:
                unresolved.append(name)
            return match.group(0)  # left literal
        return values[name]

    return ResolvedText(text=VARIABLE_PATTERN.sub(_replace, template), unresolved=unresolved)


def find_variables(template: str | None) -> list[str]:
    """Every variable name referenced by a template, in order of appearance."""
    if not template:
        return []

    seen: list[str] = []
    for match in VARIABLE_PATTERN.finditer(template):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def unknown_variables(template: str | None) -> list[str]:
    """Variables a template references that the resolver cannot fill."""
    return [name for name in find_variables(template) if name not in KNOWN_VARIABLES]
