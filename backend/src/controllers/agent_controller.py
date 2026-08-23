"""Agent endpoints.

Two shapes, deliberately. ``/agents/campaign-strategist/draft`` is typed, so
the builder gets a real response model in the OpenAPI schema and the frontend
gets generated types. ``/agents/{agent_name}/runs`` is generic, so an agent
added tomorrow is callable the moment it registers - no controller change.

Every route requires a Clerk session: a run spends money upstream, so it is
never anonymous.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.app.dependencies import AgentServiceDep, CurrentUserDep
from src.schemas.agent import AgentCatalogue, AgentRunResponse, CampaignStrategyResponse
from src.schemas.strategy import CampaignBrief
from src.services.agent_service import CAMPAIGN_STRATEGIST

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get(
    "",
    response_model=AgentCatalogue,
    summary="List the available agents",
    description=(
        "Returned whether or not agents are enabled, so a client can hide the "
        "feature instead of discovering it is off by failing a run."
    ),
)
async def list_agents(service: AgentServiceDep, user: CurrentUserDep) -> AgentCatalogue:
    return service.catalogue()


@router.post(
    f"/{CAMPAIGN_STRATEGIST}/draft",
    response_model=CampaignStrategyResponse,
    summary="Draft a campaign from a brief",
    description=(
        "Researches the business and its competitors, then returns a campaign draft "
        "shaped like `CampaignCreate` along with the analysis behind it. Anything "
        "already filled in on `existing` is preserved verbatim.\n\n"
        "Returns 503 when agents are not configured on this server."
    ),
)
async def draft_campaign(
    payload: CampaignBrief,
    service: AgentServiceDep,
    user: CurrentUserDep,
) -> CampaignStrategyResponse:
    return await service.draft_campaign(payload, user_id=user.id)


@router.post(
    "/{agent_name}/runs",
    response_model=AgentRunResponse,
    summary="Run any registered agent",
    description=(
        "Generic entry point. The body is validated against the named agent's own "
        "input schema, which `GET /agents` publishes."
    ),
)
async def run_agent(
    agent_name: str,
    payload: dict[str, Any],
    service: AgentServiceDep,
    user: CurrentUserDep,
) -> AgentRunResponse:
    return await service.run(agent_name, payload, user_id=user.id)
