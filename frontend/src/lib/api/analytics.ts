import "server-only";

import type { CampaignAnalytics } from "@/types/analytics";

import { api } from "./client";
import { getSessionToken } from "./session";

/**
 * Aggregate metrics for one campaign.
 *
 * Scoped to the owner: a campaign belonging to someone else answers 404, the
 * same as every other campaign route, so ids cannot be probed for existence.
 */
export async function getCampaignAnalytics(campaignId: string): Promise<CampaignAnalytics> {
  return api.get<CampaignAnalytics>(`/campaigns/${campaignId}/analytics`, {
    token: await getSessionToken(),
    cache: "no-store",
  });
}
