import "server-only";

import { notFound } from "next/navigation";

import { getCampaign } from "@/lib/api/campaigns";
import { isApiError } from "@/lib/api/errors";
import type { Campaign } from "@/types/campaign";

/**
 * One campaign, or the 404 page.
 *
 * The API answers 404 both for an id that does not exist and for one owned by
 * someone else - deliberately, so ids cannot be probed - and the right
 * response to either is the same not-found screen. Anything else still throws
 * and lands on the route's error boundary, because an unreachable API is not a
 * missing campaign.
 */
export async function loadCampaign(campaignId: string): Promise<Campaign> {
  try {
    return await getCampaign(campaignId);
  } catch (error) {
    if (isApiError(error) && error.status === 404) notFound();
    throw error;
  }
}
