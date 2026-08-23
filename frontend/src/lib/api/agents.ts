import "server-only";

import { cache } from "react";

import type { AgentCatalogue, CampaignBrief, CampaignStrategyResponse } from "@/types/agent";

import { api } from "./client";
import { getSessionToken } from "./session";

/**
 * The AI agents.
 *
 * Server-only like every authenticated resource. A run spends money upstream,
 * so it is never anonymous and never called from the browser directly.
 */

/**
 * What this deployment can do.
 *
 * Returned whether or not agents are switched on, so the UI can hide the
 * feature instead of discovering it is off by failing a run.
 */
export const getAgentCatalogue = cache(async (): Promise<AgentCatalogue> => {
  return api.get<AgentCatalogue>("/agents", {
    token: await getSessionToken(),
    cache: "no-store",
  });
});

/**
 * Draft a campaign from a brief.
 *
 * Slow by nature - the agent reads the business's site and its competitors -
 * so the client timeout is raised well past the default. The server has its own
 * ceiling (`AGENT_TIMEOUT_SECONDS`) and answers 504 rather than hanging.
 */
export async function draftCampaign(brief: CampaignBrief): Promise<CampaignStrategyResponse> {
  return api.post<CampaignStrategyResponse>("/agents/campaign-strategist/draft", {
    body: brief,
    token: await getSessionToken(),
    timeoutMs: 300_000,
  });
}
