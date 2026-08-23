"""The wire format shared by every agent endpoint.

An agent's *result* is its own schema - ``CampaignStrategy`` for the
strategist. What is shared is the envelope around it: which agent ran, on what
model, how long it took, what it called, and whether it got everything it asked
for. Keeping that envelope uniform means a second agent needs no new response
type, and the frontend's "the agent is thinking" affordance is written once.
"""

from typing import Any

from pydantic import Field

from src.schemas.common import StrictModel
from src.schemas.strategy import CampaignStrategy


class AgentToolCall(StrictModel):
    """One tool the agent used, so a run can be explained after the fact."""

    step: int
    tool: str
    ok: bool
    duration_ms: int
    error: str | None = None


class AgentUsageRead(StrictModel):
    """Token usage for the whole run."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class AgentRunMeta(StrictModel):
    """How the result was produced. Never needed to read the result itself."""

    agent: str
    model: str
    steps: int
    duration_ms: int
    usage: AgentUsageRead = Field(default_factory=AgentUsageRead)
    tool_calls: list[AgentToolCall] = Field(default_factory=list)

    degraded: bool = Field(
        False,
        description="True when the agent finished without everything it asked for.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description=(
            "Why it was degraded - surface these to the user, they change trust in the result."
        ),
    )


class AgentInfo(StrictModel):
    """One entry in the agent catalogue."""

    name: str
    title: str
    description: str
    toolsets: list[str] = Field(default_factory=list, description="Toolsets the agent asks for.")
    available_toolsets: list[str] = Field(
        default_factory=list,
        description=(
            "The subset this deployment can actually reach. A shortfall means degraded runs."
        ),
    )
    input_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for the run payload."
    )
    output_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema of the result."
    )


class AgentCatalogue(StrictModel):
    """Every registered agent, and whether agents are switched on at all."""

    enabled: bool
    agents: list[AgentInfo] = Field(default_factory=list)


class AgentRunResponse(StrictModel):
    """The generic run envelope: any agent, result left untyped."""

    meta: AgentRunMeta
    output: dict[str, Any]


class CampaignStrategyResponse(StrictModel):
    """The strategist's response, typed - this is what the builder calls."""

    meta: AgentRunMeta
    strategy: CampaignStrategy
