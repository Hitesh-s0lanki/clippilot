"""Loading and rendering of the Markdown prompt files.

Prompts are **not** Python string literals. Every agent's system prompt lives
in its own ``.md`` file under ``src/agents/prompts/`` so it can be read,
reviewed and diffed as prose rather than as an escaped triple-quoted blob
buried in a class body.

The rendering rule is deliberately small: ``{{name}}`` is replaced when
``name`` is one of the variables supplied, and is **left exactly as written**
when it is not. That second half matters - the campaign prompts have to teach
the model to emit the product's own personalisation token, ``{{customer_name}}``,
and a templating engine that substituted or errored on every placeholder it saw
would eat it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_SUFFIX = ".md"

# A placeholder is a bare identifier in double braces. Anything else -
# {{ customer.name }}, {{ 1 }} - is not a placeholder and is left alone.
_PLACEHOLDER = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")


class PromptNotFoundError(LookupError):
    """Raised when an agent names a prompt file that does not exist."""


class PromptLibrary:
    """Reads the prompt files once and renders them per run.

    Prompt text is cached in memory because it never changes within a process:
    ``uvicorn --reload`` watches ``src/`` and restarts when a ``.md`` file is
    edited, so a development edit is still picked up.
    """

    def __init__(self, directory: Path | None = None) -> None:
        self._directory = directory or PROMPT_DIR
        self._cache: dict[str, str] = {}

    @property
    def directory(self) -> Path:
        return self._directory

    def available(self) -> list[str]:
        """Prompt names on disk, without the ``.md`` suffix. Sorted."""
        if not self._directory.is_dir():
            return []
        return sorted(
            path.stem
            for path in self._directory.glob(f"*{PROMPT_SUFFIX}")
            if not path.stem.startswith("_") and path.stem != "README"
        )

    def load(self, name: str) -> str:
        """Return the raw text of one prompt file."""
        if name in self._cache:
            return self._cache[name]

        path = self._directory / f"{name}{PROMPT_SUFFIX}"
        # Guard against a traversal: the resolved file must stay inside the
        # prompt directory, so a name may never reach outside the package.
        if not self._is_inside(path):
            raise PromptNotFoundError(f"'{name}' is not a valid prompt name.")
        if not path.is_file():
            raise PromptNotFoundError(
                f"No prompt file at {path}. Available: {', '.join(self.available()) or 'none'}."
            )

        text = path.read_text(encoding="utf-8").strip()
        self._cache[name] = text
        return text

    def render(self, name: str, variables: Mapping[str, Any] | None = None) -> str:
        """Load ``name`` and substitute the supplied ``{{placeholders}}``.

        Values are stringified; ``None`` renders as an empty string so an
        absent optional field does not print the word "None" into a prompt.
        """
        text = self.load(name)
        if not variables:
            return text

        rendered = {key: "" if value is None else str(value) for key, value in variables.items()}

        def _substitute(match: re.Match[str]) -> str:
            key = match.group(1)
            # Unknown placeholder: hand back the original text untouched, so
            # {{customer_name}} survives to be taught to the model.
            return rendered.get(key, match.group(0))

        return _PLACEHOLDER.sub(_substitute, text)

    def _is_inside(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self._directory.resolve())
        except ValueError:
            return False
        return True
