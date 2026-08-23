"use server";

import { auth } from "@clerk/nextjs/server";
import { revalidatePath } from "next/cache";

import { toAdFailure } from "@/lib/actions/ad-field-errors";
import { changeAdStatus, createAd, deleteAd, updateAd } from "@/lib/api/ads";
import type { ActionResult } from "@/types/action";
import type { AdInput, AdStatus, AdUpdatePayload, CampaignAd } from "@/types/campaign";

/**
 * Ad mutations.
 *
 * Like the campaign actions, each one re-checks the session: a Server Action
 * is reachable by direct POST, not only through the UI.
 *
 * Failures go through `toAdFailure`, which lives in `ad-field-errors` rather
 * than here: a `"use server"` module may only export async functions, and
 * re-keying an ad's errors onto the campaign form's paths is a pure one.
 */

async function requireSession(): Promise<string | null> {
  const { userId } = await auth();
  return userId;
}

const UNAUTHENTICATED = {
  ok: false as const,
  code: "UNAUTHENTICATED",
  message: "Your session has expired. Sign in again to continue.",
  fieldErrors: {},
};

function revalidateAds(campaignId: string): void {
  revalidatePath("/dashboard");
  revalidatePath(`/campaigns/${campaignId}`, "layout");
  revalidatePath(`/preview/${campaignId}`);
  revalidatePath("/ads");
}

export async function createAdAction(
  campaignId: string,
  payload: AdInput,
): Promise<ActionResult<CampaignAd>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const ad = await createAd(campaignId, payload);
    revalidateAds(campaignId);
    return { ok: true, data: ad };
  } catch (error) {
    return toAdFailure(error);
  }
}

export async function updateAdAction(
  campaignId: string,
  adId: string,
  payload: AdUpdatePayload,
): Promise<ActionResult<CampaignAd>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const ad = await updateAd(campaignId, adId, payload);
    revalidateAds(campaignId);
    return { ok: true, data: ad };
  } catch (error) {
    return toAdFailure(error);
  }
}

/**
 * Switch an ad on, pause it, or archive it.
 *
 * Switching on rejects with the ad's own blockers when it is not finished, so
 * the caller can name the missing fields rather than saying "not ready".
 */
export async function changeAdStatusAction(
  campaignId: string,
  adId: string,
  status: AdStatus,
): Promise<ActionResult<CampaignAd>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const ad = await changeAdStatus(campaignId, adId, status);
    revalidateAds(campaignId);
    return { ok: true, data: ad };
  } catch (error) {
    return toAdFailure(error);
  }
}

export async function deleteAdAction(campaignId: string, adId: string): Promise<ActionResult> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    await deleteAd(campaignId, adId);
    revalidateAds(campaignId);
    return { ok: true, data: undefined };
  } catch (error) {
    return toAdFailure(error);
  }
}
