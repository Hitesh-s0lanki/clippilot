import "server-only";

import { cache } from "react";

import type {
  Campaign,
  CampaignPage,
  CampaignStatus,
  CampaignUpdatePayload,
  CampaignWritePayload,
} from "@/types/campaign";
import type { CampaignPreview } from "@/types/preview";

import { api } from "./client";
import { getSessionToken } from "./session";

/**
 * The authenticated campaign resource.
 *
 * Server-only: every call carries the Clerk session token, and the token is
 * read per request rather than held in a module-level variable, so one user's
 * session can never be handed to the next request on the same process.
 */

export interface ListCampaignsParams {
  /** Filters on the persisted status, not the derived `effective_status`. */
  status?: CampaignStatus;
  search?: string;
  includeArchived?: boolean;
  limit?: number;
  offset?: number;
}

export async function listCampaigns(params: ListCampaignsParams = {}): Promise<CampaignPage> {
  const { status, search, includeArchived = false, limit = 12, offset = 0 } = params;

  return api.get<CampaignPage>("/campaigns", {
    query: {
      status,
      search: search || undefined,
      include_archived: includeArchived,
      limit,
      offset,
    },
    token: await getSessionToken(),
    cache: "no-store",
  });
}

/**
 * One campaign, deduplicated per render pass.
 *
 * The `[campaignId]` layout and its pages both need the campaign - the layout
 * for the header and tabs, the page for the screen itself. `cache()` collapses
 * those into a single request instead of making the pair a reason to thread
 * the object through props.
 */
export const getCampaign = cache(async (campaignId: string): Promise<Campaign> => {
  return api.get<Campaign>(`/campaigns/${campaignId}`, {
    token: await getSessionToken(),
    cache: "no-store",
  });
});

export async function createCampaign(payload: CampaignWritePayload): Promise<Campaign> {
  return api.post<Campaign>("/campaigns", { body: payload, token: await getSessionToken() });
}

/**
 * Update the campaign itself. Its ads are updated through `@/lib/api/ads`.
 */
export async function updateCampaign(
  campaignId: string,
  payload: CampaignUpdatePayload,
): Promise<Campaign> {
  return api.patch<Campaign>(`/campaigns/${campaignId}`, {
    body: payload,
    token: await getSessionToken(),
  });
}

/**
 * Publish, pause, resume, unpublish or archive.
 *
 * Publishing enforces the full contract server-side and rejects with a 422
 * carrying one detail per unmet field, so the builder marks every blocker at
 * once rather than one per attempt.
 */
export async function changeCampaignStatus(
  campaignId: string,
  status: CampaignStatus,
): Promise<Campaign> {
  return api.post<Campaign>(`/campaigns/${campaignId}/status`, {
    body: { status },
    token: await getSessionToken(),
  });
}

export async function deleteCampaign(campaignId: string): Promise<void> {
  await api.delete<void>(`/campaigns/${campaignId}`, { token: await getSessionToken() });
}

/**
 * The owner's own preview of one ad, at any status.
 *
 * The recipient-facing route is gated on both the campaign and the ad being
 * live; this one is scoped to the owner instead, so a draft ad stays testable
 * before it is switched on. Without `adId` the campaign's primary ad is used.
 */
export const getOwnerPreview = cache(
  async (campaignId: string, memberId?: string, adId?: string): Promise<CampaignPreview> => {
    return api.get<CampaignPreview>(`/campaigns/${campaignId}/preview`, {
      query: { member_id: memberId, ad_id: adId },
      token: await getSessionToken(),
      cache: "no-store",
    });
  },
);
