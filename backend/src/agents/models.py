"""The chat model every agent runs on.

One factory, two providers. Which one runs is configuration, not code: the
agents themselves never learn the difference, because ``BaseAgent`` only ever
calls ``bind_tools`` and ``ainvoke`` - both of which LangChain gives every chat
model the same shape for.

The per-provider quirks that are easy to get wrong are handled here, once:

**Anthropic (Claude Opus 5)**

* **No ``temperature``.** Opus 5 rejects sampling parameters with a 400.
  ``ChatAnthropic`` omits the field when it is ``None``, which is the default,
  so it is simply never set.
* **No ``budget_tokens``.** The fixed thinking budget is gone; Opus 5 thinks
  adaptively whenever ``thinking`` is unset, and depth is chosen with
  ``reasoning_effort`` (the API's ``output_config.effort``) instead.
* ``max_tokens`` covers thinking as well as the answer, so the ceiling is set
  generously rather than trimmed to the expected result size.

**OpenAI (GPT-5 family)**

* **Effort has three levels, not five.** ``xhigh`` and ``max`` are Anthropic's;
  sending either to OpenAI is a validation error, so they are clamped to
  ``high`` rather than passed through and rejected.
* **No ``temperature`` either.** The reasoning models accept only the default,
  and ``ChatOpenAI`` omits the field when it is ``None``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.app.errors import ApiError
from src.core.config import Settings

if TYPE_CHECKING:  # pragma: no cover
    from langchain_core.language_models import BaseChatModel

# Effort levels OpenAI accepts. Anthropic adds `xhigh` and `max` above these.
_OPENAI_EFFORT = {"low", "medium", "high"}


def _openai_effort(effort: str) -> str:
    """Clamp an Anthropic-shaped effort level to what OpenAI accepts."""
    return effort if effort in _OPENAI_EFFORT else "high"


def build_chat_model(
    settings: Settings,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    effort: str | None = None,
) -> BaseChatModel:
    """Return the chat model, or refuse clearly when no key is configured.

    Raising 503 rather than 500 is the honest status: the request was fine,
    this deployment simply has the agents switched off.
    """
    provider = settings.agent_provider_resolved

    if provider is None:
        raise ApiError(
            503,
            "AGENTS_NOT_CONFIGURED",
            "AI agents are not enabled on this server. Set ANTHROPIC_API_KEY or "
            "OPENAI_API_KEY to turn them on.",
        )

    resolved_model = model or settings.agent_model_resolved
    resolved_tokens = max_tokens or settings.agent_max_tokens
    resolved_effort = effort or settings.agent_effort

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=resolved_model,
            api_key=settings.anthropic_api_key,
            max_tokens=resolved_tokens,
            reasoning_effort=resolved_effort,  # type: ignore[arg-type]
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=resolved_model,
        api_key=settings.openai_api_key,
        max_tokens=resolved_tokens,
        reasoning_effort=_openai_effort(resolved_effort),
    )
