"use server";

import { auth } from "@clerk/nextjs/server";
import { revalidatePath } from "next/cache";

import { draftCampaign } from "@/lib/api/agents";
import { createCampaign } from "@/lib/api/campaigns";
import { isApiError } from "@/lib/api/errors";
import type { ActionResult } from "@/types/action";
import type { CampaignBrief, CampaignStrategyResponse } from "@/types/agent";
import type { Campaign, CampaignWritePayload } from "@/types/campaign";

/**
 * The campaign strategist.
 *
 * Two steps, deliberately separate. Generating is slow and costs money
 * upstream; creating is instant and irreversible. Keeping them apart means the
 * user reads what the agent produced and picks an audience before anything is
 * written, and a rejected draft costs nothing but the run.
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

/** Research the business and draft a campaign. Writes nothing. */
export async function draftCampaignAction(
  brief: CampaignBrief,
): Promise<ActionResult<CampaignStrategyResponse>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    return { ok: true, data: await draftCampaign(brief) };
  } catch (error) {
    return toFailure(error);
  }
}

/**
 * Create the campaign the user accepted, with its drafted ads.
 *
 * One call: `POST /campaigns` takes the ads inline, so the whole draft lands
 * together and the user arrives at a campaign that already has its creatives
 * to finish - rather than an empty one and a list to retype.
 */
export async function createFromDraftAction(
  payload: CampaignWritePayload,
): Promise<ActionResult<Campaign>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const campaign = await createCampaign(payload);
    revalidatePath("/dashboard");
    revalidatePath(`/campaigns/${campaign.id}`, "layout");
    return { ok: true, data: campaign };
  } catch (error) {
    return toFailure(error);
  }
}
