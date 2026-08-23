import type { CampaignPreview, PreviewEvent, ResponseResult } from "@/types/preview";
import type { PublicCampaignPage } from "@/types/public";

import { api } from "./client";

/**
 * The recipient-facing endpoints.
 *
 * Unauthenticated by design - a customer opening a video journey has no Clerk
 * session - so nothing here reads a token, and nothing here imports
 * `./session`. That is what keeps this module importable from the browser,
 * where the response click actually happens.
 */

export interface ListPublicCampaignsInput {
  limit?: number;
  offset?: number;
}

/**
 * The ads library: every campaign that is live right now, newest first.
 *
 * Needs no id and no session, so it is the one public read that anyone can
 * reach by typing a URL. Left uncached because a campaign leaves the listing
 * the moment its owner pauses it.
 */
export function listPublicCampaigns(
  { limit, offset }: ListPublicCampaignsInput = {},
  signal?: AbortSignal,
): Promise<PublicCampaignPage> {
  return api.get<PublicCampaignPage>("/public/campaigns", {
    query: { limit, offset },
    cache: "no-store",
    signal,
  });
}

export function getPublicPreview(
  campaignId: string,
  memberId?: string | null,
  signal?: AbortSignal,
  adId?: string | null,
): Promise<CampaignPreview> {
  return api.get<CampaignPreview>(`/public/campaigns/${campaignId}`, {
    query: { member_id: memberId ?? undefined, ad_id: adId ?? undefined },
    cache: "no-store",
    signal,
  });
}

export interface RecordEventInput {
  campaignId: string;
  /** Stable for one preview session. The server's deduplication key. */
  sessionId: string;
  /** Which creative was on screen. Without it the primary ad is assumed. */
  adId?: string | null;
  /** Who is watching. Without it the copy falls back to its neutral form. */
  memberId?: string | null;
}

/** Idempotent per session: a repeat call returns the original event, not an error. */
export function recordView({
  campaignId,
  sessionId,
  adId,
  memberId,
}: RecordEventInput): Promise<PreviewEvent> {
  return api.post<PreviewEvent>(`/public/campaigns/${campaignId}/views`, {
    body: { session_id: sessionId, ad_id: adId ?? null, member_id: memberId ?? null },
  });
}

export interface RecordResponseInput extends RecordEventInput {
  optionId: string;
}

/**
 * Records a response and returns the follow-up to render.
 *
 * Also idempotent per session, and deliberately so: a double-click returns the
 * follow-up for the option originally chosen rather than switching the outcome.
 */
export function recordResponse({
  campaignId,
  sessionId,
  optionId,
  adId,
  memberId,
}: RecordResponseInput): Promise<ResponseResult> {
  return api.post<ResponseResult>(`/public/campaigns/${campaignId}/responses`, {
    body: {
      session_id: sessionId,
      option_id: optionId,
      ad_id: adId ?? null,
      member_id: memberId ?? null,
    },
  });
}
