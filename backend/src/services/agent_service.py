"""Agent orchestration.

Thin on purpose. The agents own their own behaviour; this service owns the
things that are the *application's* business rather than any one agent's:
whether agents are enabled at all, resolving a name to a class, validating an
untrusted payload against that agent's own input schema, and flattening a run
into the wire envelope.

No FastAPI import, in keeping with the rest of ``src/services``: it raises
``ApiError`` and the registered handler turns that into a response.
"""

from __future__ import annotations

from typing import Any

from src.agents import registry
from src.agents.base import AgentContext, AgentRun, BaseAgent
from src.agents.prompts import PromptLibrary
from src.agents.toolkits import AgentToolkit
from src.app.errors import ApiError
from src.core.config import Settings
from src.schemas.agent import (
    AgentCatalogue,
    AgentInfo,
    AgentRunMeta,
    AgentRunResponse,
    AgentToolCall,
    AgentUsageRead,
    CampaignStrategyResponse,
)
from src.schemas.strategy import CampaignBrief, CampaignStrategy

CAMPAIGN_STRATEGIST = "campaign-strategist"


class AgentService:
    def __init__(
        self,
        settings: Settings,
        *,
        toolkit: AgentToolkit | None = None,
        prompts: PromptLibrary | None = None,
    ) -> None:
        self._settings = settings
        self._toolkit = toolkit or AgentToolkit(settings)
        self._prompts = prompts or PromptLibrary()

    # --- catalogue ---------------------------------------------------------

    def catalogue(self) -> AgentCatalogue:
        """List every agent, and what this deployment can actually do.

        Returned whether or not agents are enabled, so the frontend can hide
        the feature rather than discovering it is off by failing a run.
        """
        available = sorted(self._toolkit.configured)
        return AgentCatalogue(
            enabled=self._settings.agents_configured,
            agents=[
                AgentInfo(
                    name=agent.name,
                    title=agent.title,
                    description=agent.description,
                    toolsets=list(agent.toolsets),
                    available_toolsets=[t for t in agent.toolsets if t in available],
                    input_schema=agent.input_model.model_json_schema(),
                    output_schema=agent.output_model.model_json_schema(),
                )
                for agent in registry.all_agents()
            ],
        )

    # --- runs --------------------------------------------------------------

    async def run(self, name: str, payload: Any, *, user_id: str) -> AgentRunResponse:
        """Run any registered agent against an untrusted payload."""
        agent = self._build(name)
        brief = agent.parse_payload(payload)
        run = await agent.run(brief, context=AgentContext(user_id=user_id))

        return AgentRunResponse(
            meta=_meta(run),
            output=run.output.model_dump(mode="json"),
        )

    async def draft_campaign(
        self, brief: CampaignBrief, *, user_id: str
    ) -> CampaignStrategyResponse:
        """Run the strategist, typed - the endpoint the builder calls."""
        agent = self._build(CAMPAIGN_STRATEGIST)
        run = await agent.run(brief, context=AgentContext(user_id=user_id))

        if not isinstance(run.output, CampaignStrategy):  # pragma: no cover - registry mismatch
            raise ApiError(
                500,
                "AGENT_CONTRACT_MISMATCH",
                f"'{CAMPAIGN_STRATEGIST}' did not return a campaign strategy.",
            )

        return CampaignStrategyResponse(meta=_meta(run), strategy=run.output)

    # --- internals ---------------------------------------------------------

    def _build(self, name: str) -> BaseAgent:
        """Resolve a name to a ready agent, refusing early when disabled.

        Checked here rather than at the model call so a disabled deployment
        answers immediately instead of after loading tools it cannot use.
        """
        if not self._settings.agents_configured:
            raise ApiError(
                503,
                "AGENTS_NOT_CONFIGURED",
                "AI agents are not enabled on this server. Set ANTHROPIC_API_KEY or "
                "OPENAI_API_KEY to turn them on.",
            )

        return registry.get(name)(
            self._settings,
            toolkit=self._toolkit,
            prompts=self._prompts,
        )


def _meta(run: AgentRun) -> AgentRunMeta:
    return AgentRunMeta(
        agent=run.agent,
        model=run.model,
        steps=run.steps,
        duration_ms=run.duration_ms,
        usage=AgentUsageRead(
            input_tokens=run.usage.input_tokens,
            output_tokens=run.usage.output_tokens,
            total_tokens=run.usage.total_tokens,
        ),
        tool_calls=[
            AgentToolCall(
                step=record.step,
                tool=record.tool,
                ok=record.ok,
                duration_ms=record.duration_ms,
                error=record.error,
            )
            for record in run.tool_calls
        ],
        degraded=run.degraded,
        notes=run.notes,
    )
