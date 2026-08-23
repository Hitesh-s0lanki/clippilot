"use server";

import { auth } from "@clerk/nextjs/server";
import { revalidatePath } from "next/cache";

import {
  addMembers,
  createAudience,
  deleteAudience,
  removeMember,
  updateAudience,
} from "@/lib/api/audiences";
import { isApiError } from "@/lib/api/errors";
import type { ActionResult } from "@/types/action";
import type {
  AudienceWritePayload,
  AudienceImportResult,
  AudienceMemberInput,
  Audience,
  AudienceUpdatePayload,
} from "@/types/audience";

/**
 * Audience mutations.
 *
 * Like every Server Action here, each one re-checks the session: an action is
 * reachable by direct POST, not only through the UI.
 *
 * Revalidation is broad on purpose. An audience is account-level and any
 * number of campaigns point at it, so a membership change moves the member
 * count on every campaign that selected it — and `member_count` is what
 * decides whether those campaigns can publish.
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

function revalidateAudiences(audienceId?: string): void {
  revalidatePath("/dashboard");
  revalidatePath("/audiences");
  if (audienceId) revalidatePath(`/audiences/${audienceId}`);
  // Any campaign may be pointing at this list, and its publishability moves
  // with the member count.
  revalidatePath("/campaigns", "layout");
}

export async function createAudienceAction(
  payload: AudienceWritePayload,
): Promise<ActionResult<Audience>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const audience = await createAudience(payload);
    revalidateAudiences(audience.id);
    return { ok: true, data: audience };
  } catch (error) {
    return toFailure(error);
  }
}

export async function updateAudienceAction(
  audienceId: string,
  payload: AudienceUpdatePayload,
): Promise<ActionResult<Audience>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const audience = await updateAudience(audienceId, payload);
    revalidateAudiences(audienceId);
    return { ok: true, data: audience };
  } catch (error) {
    return toFailure(error);
  }
}

/**
 * Add people in bulk.
 *
 * Resolves successfully on a *partial* import: one repeated email in a 200-row
 * file costs that row, not the file, and the result names every row that did
 * not land so the caller can show them.
 */
export async function addMembersAction(
  audienceId: string,
  members: AudienceMemberInput[],
): Promise<ActionResult<AudienceImportResult>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    const result = await addMembers(audienceId, members);
    revalidateAudiences(audienceId);
    return { ok: true, data: result };
  } catch (error) {
    return toFailure(error);
  }
}

export async function removeMemberAction(
  audienceId: string,
  memberId: string,
): Promise<ActionResult> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    await removeMember(audienceId, memberId);
    revalidateAudiences(audienceId);
    return { ok: true, data: undefined };
  } catch (error) {
    return toFailure(error);
  }
}

export async function deleteAudienceAction(audienceId: string): Promise<ActionResult> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    await deleteAudience(audienceId);
    revalidateAudiences();
    return { ok: true, data: undefined };
  } catch (error) {
    return toFailure(error);
  }
}
