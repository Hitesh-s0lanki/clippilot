import "server-only";

import { cache } from "react";

import type { AdInput, AdList, AdStatus, AdUpdatePayload, CampaignAd } from "@/types/campaign";

import { api } from "./client";
import { getSessionToken } from "./session";

/**
 * The authenticated ad resource, nested under its campaign.
 *
 * Server-only, like every authenticated resource: the Clerk token is read per
 * request rather than held in a module-level variable, so one user's session
 * can never be handed to the next request on the same process.
 *
 * Ads live here rather than on the campaign payload because a campaign owns
 * several of them, and replacing the whole list by index on every campaign
 * PATCH would silently reorder or drop creatives.
 */

export const listAds = cache(async (campaignId: string): Promise<AdList> => {
  return api.get<AdList>(`/campaigns/${campaignId}/ads`, {
    token: await getSessionToken(),
    cache: "no-store",
  });
});

export const getAd = cache(async (campaignId: string, adId: string): Promise<CampaignAd> => {
  return api.get<CampaignAd>(`/campaigns/${campaignId}/ads/${adId}`, {
    token: await getSessionToken(),
    cache: "no-store",
  });
});

export async function createAd(campaignId: string, payload: AdInput): Promise<CampaignAd> {
  return api.post<CampaignAd>(`/campaigns/${campaignId}/ads`, {
    body: payload,
    token: await getSessionToken(),
  });
}

export async function updateAd(
  campaignId: string,
  adId: string,
  payload: AdUpdatePayload,
): Promise<CampaignAd> {
  return api.patch<CampaignAd>(`/campaigns/${campaignId}/ads/${adId}`, {
    body: payload,
    token: await getSessionToken(),
  });
}

/**
 * Switch an ad on, pause it, or archive it.
 *
 * Switching one on enforces that ad's own completeness contract and rejects
 * with a 422 carrying one detail per unmet field. An ad still only delivers
 * while its campaign is live - that is what `effective_status` reports.
 */
export async function changeAdStatus(
  campaignId: string,
  adId: string,
  status: AdStatus,
): Promise<CampaignAd> {
  return api.post<CampaignAd>(`/campaigns/${campaignId}/ads/${adId}/status`, {
    body: { status },
    token: await getSessionToken(),
  });
}

export async function deleteAd(campaignId: string, adId: string): Promise<void> {
  await api.delete<void>(`/campaigns/${campaignId}/ads/${adId}`, {
    token: await getSessionToken(),
  });
}
