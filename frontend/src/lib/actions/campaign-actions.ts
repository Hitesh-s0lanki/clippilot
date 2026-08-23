"use server";

import { auth } from "@clerk/nextjs/server";
import { revalidatePath } from "next/cache";

import {
  changeCampaignStatus,
  createCampaign,
  deleteCampaign,
  updateCampaign,
} from "@/lib/api/campaigns";
import { isApiError } from "@/lib/api/errors";
import type { ActionResult } from "@/types/action";
import type { Campaign, CampaignStatus, CampaignWritePayload } from "@/types/campaign";

/**
 * Campaign mutations.
 *
 * Server Actions are reachable by direct POST, not only through the UI, so
 * each one re-checks the session before touching the API - the proxy and the
 * route-group guard protect documents, not these.
 *
 * Every action funnels failures through `toFailure`, which keeps the backend's
 * field-level details intact. That is what lets the publish contract report
 * all of its blockers at once instead of one per attempt.
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

function toFailure(error: unknown): Extract<ActionResult, { ok: false }> {
  if (isApiError(error)) {
    return {
      ok: false,
      code: error.code,
      message: error.message,
      fieldErrors: error.fieldErrors(),
    };
  }

  return {
    ok: false,
    code: "UNEXPECTED_ERROR",
    message: "Something went wrong. Try again.",
    fieldErrors: {},
  };
}

/** Refreshes every screen a campaign appears on after it changes. */
function revalidateCampaign(campaignId?: string): void {
  revalidatePath("/dashboard");
  if (campaignId) {
    revalidatePath(`/campaigns/${campaignId}`, "layout");
    revalidatePath(`/preview/${campaignId}`);
  }
}

export async function createCampaignAction(
  payload: CampaignWritePayload,
): Promise<ActionResult<Campaign>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const campaign = await createCampaign(payload);
    revalidateCampaign(campaign.id);
    return { ok: true, data: campaign };
  } catch (error) {
    return toFailure(error);
  }
}

export async function updateCampaignAction(
  campaignId: string,
  payload: Partial<CampaignWritePayload>,
): Promise<ActionResult<Campaign>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const campaign = await updateCampaign(campaignId, payload);
    revalidateCampaign(campaign.id);
    return { ok: true, data: campaign };
  } catch (error) {
    return toFailure(error);
  }
}

/**
 * Saves the draft and then publishes it, so the button acts on what is on
 * screen rather than on whatever was last saved. A publish rejection leaves
 * the save intact - nothing is lost, and the blockers name what to fix.
 */
export async function saveAndPublishAction(
  campaignId: string,
  payload: Partial<CampaignWritePayload>,
): Promise<ActionResult<Campaign>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    await updateCampaign(campaignId, payload);
    const campaign = await changeCampaignStatus(campaignId, "ACTIVE");
    revalidateCampaign(campaign.id);
    return { ok: true, data: campaign };
  } catch (error) {
    return toFailure(error);
  }
}

export async function changeCampaignStatusAction(
  campaignId: string,
  status: CampaignStatus,
): Promise<ActionResult<Campaign>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const campaign = await changeCampaignStatus(campaignId, status);
    revalidateCampaign(campaign.id);
    return { ok: true, data: campaign };
  } catch (error) {
    return toFailure(error);
  }
}

export async function deleteCampaignAction(campaignId: string): Promise<ActionResult> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    await deleteCampaign(campaignId);
    revalidateCampaign(campaignId);
    return { ok: true, data: undefined };
  } catch (error) {
    return toFailure(error);
  }
}
