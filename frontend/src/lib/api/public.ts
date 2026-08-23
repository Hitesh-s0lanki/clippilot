import type { CampaignPreview, PreviewEvent, ResponseResult } from "@/types/preview";

import { api } from "./client";

/**
 * The recipient-facing endpoints.
 *
 * Unauthenticated by design - a customer opening a video journey has no Clerk
 * session - so nothing here reads a token, and nothing here imports
 * `./session`. That is what keeps this module importable from the browser,
 * where the response click actually happens.
 */

export function getPublicPreview(
  campaignId: string,
  recipientId?: string | null,
  signal?: AbortSignal,
): Promise<CampaignPreview> {
  return api.get<CampaignPreview>(`/public/campaigns/${campaignId}`, {
    query: { recipient_id: recipientId ?? undefined },
    cache: "no-store",
    signal,
  });
}

export interface RecordEventInput {
  campaignId: string;
  /** Stable for one preview session. The server's deduplication key. */
  sessionId: string;
  recipientId?: string | null;
}

/** Idempotent per session: a repeat call returns the original event, not an error. */
export function recordView({
  campaignId,
  sessionId,
  recipientId,
}: RecordEventInput): Promise<PreviewEvent> {
  return api.post<PreviewEvent>(`/public/campaigns/${campaignId}/views`, {
    body: { session_id: sessionId, recipient_id: recipientId ?? null },
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
  recipientId,
}: RecordResponseInput): Promise<ResponseResult> {
  return api.post<ResponseResult>(`/public/campaigns/${campaignId}/responses`, {
    body: { session_id: sessionId, option_id: optionId, recipient_id: recipientId ?? null },
  });
}
