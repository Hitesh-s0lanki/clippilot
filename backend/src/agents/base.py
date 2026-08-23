"""``BaseAgent`` - the contract every agent in this codebase implements.

A subclass declares *what* it is (a name, a prompt file, an input schema and an
output schema) and answers a couple of small hooks. This class owns everything
else: prompt rendering, tool loading, the tool-calling loop, validation,
timeouts, token accounting and error mapping. Writing the second agent should
be a schema, a Markdown prompt and about thirty lines of Python.

Two design decisions are worth stating outright, because both had an obvious
alternative that does not hold up.

**Structured output is a terminal tool, not ``with_structured_output``.**
The natural-looking approach - research with tools, then make a second call
constrained to the schema - forces ``tool_choice`` on that second call, and a
forced tool choice conflicts with the extended thinking that Opus 5 runs by
default. It also pays for the whole transcript twice. Instead the output schema
is bound as one more tool alongside the research tools, and the run finishes
when the model calls it. One loop, no forced choice, no second billing of the
context, and the model can interleave "look something up" and "I am ready to
answer" as it sees fit.

**A rejected result is repaired, not raised.** When the model's arguments fail
Pydantic validation, the errors are handed back as a tool result and the model
gets another turn. Schemas this wide - a whole campaign draft plus its research
- fail on a detail far more often than on the substance, and re-prompting costs
one turn where failing costs the user the entire run.

Research degrades rather than fails: if Firecrawl is unreachable the agent
still answers from the user's brief, and the run is flagged ``degraded`` with a
note explaining what was missing.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, ValidationError

from src.agents.models import build_chat_model
from src.agents.prompts import PromptLibrary
from src.agents.toolkits import AgentToolkit
from src.app.errors import ApiError
from src.core.config import Settings

if TYPE_CHECKING:  # pragma: no cover
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
    from langchain_core.tools import BaseTool

logger = logging.getLogger("clippilot.agents")

# One scraped page can run to hundreds of kilobytes. Past this many characters
# a tool result is truncated, so a single greedy fetch cannot crowd the brief
# and the accumulated research out of the context window.
MAX_TOOL_RESULT_CHARS = 24_000

# How many times the model may reply with prose instead of calling a tool
# before the run is abandoned.
MAX_NUDGES = 2


@dataclass(frozen=True)
class AgentContext:
    """Who and what a run is for. Never sent to the model."""

    user_id: str | None = None
    campaign_id: str | None = None


@dataclass(frozen=True)
class ToolCallRecord:
    """One tool invocation, kept so a run can be explained after the fact."""

    step: int
    tool: str
    arguments: dict[str, Any]
    ok: bool
    duration_ms: int
    error: str | None = None


@dataclass(frozen=True)
class AgentUsage:
    """Token usage summed across every turn of one run."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def plus(self, message: AIMessage) -> AgentUsage:
        usage = getattr(message, "usage_metadata", None) or {}
        return replace(
            self,
            input_tokens=self.input_tokens + int(usage.get("input_tokens", 0) or 0),
            output_tokens=self.output_tokens + int(usage.get("output_tokens", 0) or 0),
        )


@dataclass(frozen=True)
class AgentRun[OutputT: BaseModel]:
    """A completed run: the validated result, and how it was arrived at."""

    agent: str
    model: str
    output: OutputT
    steps: int
    duration_ms: int
    usage: AgentUsage = field(default_factory=AgentUsage)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def degraded(self) -> bool:
        """True when the run finished without everything it asked for."""
        return bool(self.notes)


class BaseAgent[InputT: BaseModel, OutputT: BaseModel](ABC):
    """Base class for every agent.

    Subclasses set the class-level declarations and implement
    :meth:`opening_message`. Everything else has a working default.
    """

    # --- identity ----------------------------------------------------------
    #: URL-safe identifier, unique across the registry. kebab-case.
    name: ClassVar[str]
    #: Human label for the agent catalogue.
    title: ClassVar[str]
    #: One sentence, shown in the catalogue and in the OpenAPI schema.
    description: ClassVar[str]

    # --- contract ----------------------------------------------------------
    #: Prompt file under ``src/agents/prompts/``, without the ``.md`` suffix.
    prompt_file: ClassVar[str]
    #: Schema the caller's payload is validated against.
    input_model: ClassVar[type[BaseModel]]
    #: Schema the agent must return. Bound as the terminal tool.
    output_model: ClassVar[type[BaseModel]]

    # --- capabilities ------------------------------------------------------
    #: Toolset names from ``src.agents.toolkits``, e.g. ``(FIRECRAWL,)``.
    toolsets: ClassVar[tuple[str, ...]] = ()
    #: Per-agent overrides; ``None`` defers to Settings.
    max_steps: ClassVar[int | None] = None
    max_tokens: ClassVar[int | None] = None
    effort: ClassVar[str | None] = None
    timeout_seconds: ClassVar[float | None] = None

    def __init__(
        self,
        settings: Settings,
        *,
        toolkit: AgentToolkit | None = None,
        prompts: PromptLibrary | None = None,
        chat_model: BaseChatModel | None = None,
    ) -> None:
        self._settings = settings
        self._toolkit = toolkit or AgentToolkit(settings)
        self._prompts = prompts or PromptLibrary()
        # Injectable so tests can drive the loop without a network call.
        self._chat_model = chat_model

    # --- hooks -------------------------------------------------------------

    @abstractmethod
    def opening_message(self, payload: InputT) -> str:
        """The first user turn: the caller's request, written out for the model."""

    def prompt_variables(self, payload: InputT) -> dict[str, Any]:
        """Values for the ``{{placeholders}}`` in the prompt file.

        ``output_tool`` and ``research_tools`` are always supplied on top of
        whatever a subclass returns, so a prompt can name them without the
        subclass having to know how the loop is wired.
        """
        return {}

    def finalise(self, output: OutputT, payload: InputT) -> OutputT:
        """Last chance to correct the model's result before it is returned.

        Use it for rules that are cheaper to enforce in code than to explain in
        a prompt - clamping a value the model is prone to overshooting, say.
        """
        return output

    # --- run ---------------------------------------------------------------

    @property
    def output_tool(self) -> str:
        """The tool name the model calls to finish. Derived from the schema."""
        return self.output_model.__name__

    def parse_payload(self, raw: Any) -> InputT:
        """Validate an untrusted payload against this agent's input schema."""
        try:
            return self.input_model.model_validate(raw)  # type: ignore[return-value]
        except ValidationError as exc:
            from src.app.errors import normalise_validation_errors

            raise ApiError(
                422,
                "VALIDATION_ERROR",
                f"The payload for '{self.name}' failed validation.",
                normalise_validation_errors(exc.errors()),
            ) from exc

    async def run(
        self, payload: InputT, *, context: AgentContext | None = None
    ) -> AgentRun[OutputT]:
        """Execute the agent and return its validated result."""
        timeout = self.timeout_seconds or self._settings.agent_timeout_seconds
        started = time.monotonic()
        try:
            async with asyncio.timeout(timeout):
                return await self._run(payload, context or AgentContext(), started)
        except TimeoutError as exc:
            raise ApiError(
                504,
                "AGENT_TIMEOUT",
                f"The {self.title} did not finish within {timeout:.0f}s. Try a narrower brief.",
            ) from exc

    async def _run(
        self, payload: InputT, context: AgentContext, started: float
    ) -> AgentRun[OutputT]:
        from langchain_core.messages import HumanMessage, SystemMessage

        loaded = await self._toolkit.load(self.toolsets)
        tools_by_name = {tool.name: tool for tool in loaded.tools}

        model = self._chat_model or build_chat_model(
            self._settings,
            max_tokens=self.max_tokens,
            effort=self.effort,
        )
        # The output schema rides alongside the research tools; calling it is
        # how the model says "done". See the module docstring.
        bound = model.bind_tools([*loaded.tools, self.output_model])

        messages: list[BaseMessage] = [
            SystemMessage(content=self._system_prompt(payload, sorted(tools_by_name))),
            HumanMessage(content=self.opening_message(payload)),
        ]

        records: list[ToolCallRecord] = []
        usage = AgentUsage()
        nudges = 0
        max_steps = self.max_steps or self._settings.agent_max_steps

        for step in range(1, max_steps + 1):
            reply = await self._think(bound, messages)
            messages.append(reply)
            usage = usage.plus(reply)

            calls = list(getattr(reply, "tool_calls", None) or [])
            if not calls:
                nudges += 1
                if nudges > MAX_NUDGES:
                    raise ApiError(
                        502,
                        "AGENT_NO_RESULT",
                        f"The {self.title} finished without returning a result.",
                    )
                messages.append(HumanMessage(content=self._closing_instruction()))
                continue

            submitted: OutputT | None = None
            accepted: dict[int, ToolMessage] = {}
            research: list[tuple[int, dict[str, Any]]] = []

            for index, call in enumerate(calls):
                if call.get("name") == self.output_tool:
                    submitted, accepted[index] = self._accept(call)
                else:
                    research.append((index, call))

            # A model that asks for three lookups in one turn expects three
            # lookups, not three round trips: running them in sequence turned
            # 6 + 6 + 6 seconds into eighteen. Results are re-ordered back to
            # the order they were asked for, so the transcript still reads as
            # the model wrote it.
            fetched = await asyncio.gather(
                *(self._call_tool(tools_by_name, call, step) for _, call in research)
            )
            by_index = {index: result for (index, _), result in zip(research, fetched, strict=True)}

            for index in range(len(calls)):
                if index in accepted:
                    messages.append(accepted[index])
                    continue
                record, tool_message = by_index[index]
                records.append(record)
                messages.append(tool_message)

            if submitted is not None:
                return AgentRun(
                    agent=self.name,
                    model=getattr(model, "model", self._settings.agent_model_resolved),
                    output=self.finalise(submitted, payload),
                    steps=step,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    usage=usage,
                    tool_calls=records,
                    notes=loaded.notes,
                )

        raise ApiError(
            504,
            "AGENT_STEP_LIMIT",
            f"The {self.title} used all {max_steps} of its steps without returning a result.",
        )

    # --- internals ---------------------------------------------------------

    def _system_prompt(self, payload: InputT, tool_names: list[str]) -> str:
        variables = {
            **self.prompt_variables(payload),
            "output_tool": self.output_tool,
            "research_tools": ", ".join(tool_names) if tool_names else "none available",
        }
        return self._prompts.render(self.prompt_file, variables)

    def _closing_instruction(self) -> str:
        return (
            f"Do not reply with prose. Call the `{self.output_tool}` tool now with your "
            f"complete result, using your best judgement for anything you could not verify."
        )

    async def _think(self, bound: Any, messages: list[BaseMessage]) -> AIMessage:
        """One model turn, with upstream failures mapped to a clean error."""
        try:
            return await bound.ainvoke(messages)
        except ApiError:
            raise
        except Exception as exc:  # noqa: BLE001 - one boundary for every provider error
            logger.exception("agent %s: model call failed", self.name)
            raise ApiError(
                502,
                "AGENT_UPSTREAM_ERROR",
                f"The {self.title} could not reach the language model.",
            ) from exc

    def _accept(self, call: dict[str, Any]) -> tuple[OutputT | None, ToolMessage]:
        """Validate the model's final answer, or hand back the errors to fix."""
        from langchain_core.messages import ToolMessage

        try:
            output = self.output_model.model_validate(call.get("args") or {})
        except ValidationError as exc:
            logger.info("agent %s: result rejected, asking for a correction", self.name)
            return None, ToolMessage(
                content=(
                    "Rejected - the result did not match the schema. Fix these and call "
                    f"`{self.output_tool}` again:\n{exc}"
                ),
                tool_call_id=call.get("id", ""),
                status="error",
            )

        return output, ToolMessage(  # type: ignore[return-value]
            content="Accepted.",
            tool_call_id=call.get("id", ""),
        )

    async def _call_tool(
        self,
        tools_by_name: dict[str, BaseTool],
        call: dict[str, Any],
        step: int,
    ) -> tuple[ToolCallRecord, ToolMessage]:
        """Invoke one research tool, recording what happened either way."""
        from langchain_core.messages import ToolMessage

        name = str(call.get("name", ""))
        arguments = dict(call.get("args") or {})
        started = time.monotonic()

        tool = tools_by_name.get(name)
        if tool is None:
            # The model invented a tool. Say so plainly and let it continue.
            return (
                ToolCallRecord(
                    step, name, arguments, ok=False, duration_ms=0, error="unknown tool"
                ),
                ToolMessage(
                    content=(
                        f"No tool named `{name}`. Available: {', '.join(tools_by_name) or 'none'}."
                    ),
                    tool_call_id=call.get("id", ""),
                    status="error",
                ),
            )

        # Bounded individually, not just by the run's own ceiling. One page
        # that never responds would otherwise hold the whole run until the
        # global timeout and lose the research already done - which is exactly
        # how a single slow site used to kill an entire draft.
        limit = self._settings.agent_tool_timeout_seconds

        try:
            async with asyncio.timeout(limit):
                message = await tool.ainvoke(call)
        except TimeoutError:
            elapsed = int((time.monotonic() - started) * 1000)
            logger.warning("agent %s: tool %s timed out after %.0fs", self.name, name, limit)
            return (
                ToolCallRecord(
                    step,
                    name,
                    arguments,
                    ok=False,
                    duration_ms=elapsed,
                    error=f"timed out after {limit:.0f}s",
                ),
                ToolMessage(
                    content=(
                        f"`{name}` timed out after {limit:.0f}s. Continue without it - "
                        f"do not retry the same target."
                    ),
                    tool_call_id=call.get("id", ""),
                    status="error",
                ),
            )
        except Exception as exc:  # noqa: BLE001 - a failed lookup is not a failed run
            elapsed = int((time.monotonic() - started) * 1000)
            logger.warning("agent %s: tool %s failed: %s", self.name, name, exc)
            return (
                ToolCallRecord(
                    step, name, arguments, ok=False, duration_ms=elapsed, error=str(exc)
                ),
                ToolMessage(
                    content=f"`{name}` failed: {exc}. Continue without it.",
                    tool_call_id=call.get("id", ""),
                    status="error",
                ),
            )

        elapsed = int((time.monotonic() - started) * 1000)
        message.content = _truncate(message.content)
        ok = getattr(message, "status", "success") != "error"
        return (
            ToolCallRecord(
                step,
                name,
                arguments,
                ok=ok,
                duration_ms=elapsed,
                error=None if ok else str(message.content)[:200],
            ),
            message,
        )


def _truncate(content: Any) -> str:
    """Flatten a tool result to text and cap it. See MAX_TOOL_RESULT_CHARS."""
    text = content if isinstance(content, str) else str(content)
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text
    return (
        text[:MAX_TOOL_RESULT_CHARS]
        + f"\n\n[truncated - {len(text) - MAX_TOOL_RESULT_CHARS} more characters. "
        + "Fetch a narrower target if you need the rest.]"
    )
