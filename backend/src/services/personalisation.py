"""Variable substitution for personalised copy.

The brief mandates ``{{customer_name}}``. The resolver is generalised so the
same substitution runs over the headline, the personalised message and the
follow-up copy.

Resolution rules:

- Unknown variable -> left literal and reported, never blanked, never a 500.
- Missing recipient value -> falls back to "there", so a preview is never broken.
- Whitespace inside the braces is tolerated: ``{{ customer_name }}`` resolves.
- Escaping is a render-time concern; storage keeps what the user typed.
"""

import re
from dataclasses import dataclass, field

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

MISSING_NAME_FALLBACK = "there"

KNOWN_VARIABLES = frozenset({"customer_name", "campaign_name", "option_label"})


@dataclass(slots=True)
class PersonalisationContext:
    """Values available to the resolver for one render."""

    customer_name: str | None = None
    campaign_name: str | None = None
    option_label: str | None = None

    def as_mapping(self) -> dict[str, str]:
        return {
            "customer_name": self.customer_name or MISSING_NAME_FALLBACK,
            "campaign_name": self.campaign_name or "",
            "option_label": self.option_label or "",
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
