"use server";

import { auth } from "@clerk/nextjs/server";

import { isApiError } from "@/lib/api/errors";
import { completeVideoUpload, createVideoUploadTicket } from "@/lib/api/uploads";
import type { ActionResult } from "@/types/action";
import type { VideoUploadRequest, VideoUploadResult, VideoUploadTicket } from "@/types/upload";

/**
 * The two authenticated ends of a video upload.
 *
 * Server Actions rather than a client-side API module, so the Clerk token is
 * never handed to the browser: the builder is a Client Component, and reading
 * a session token there to sign a request would put it in the bundle's reach
 * for no benefit. The one call the browser does make - the file to S3 - needs
 * no ClipPilot credential at all, only the signed policy these return.
 *
 * Like the campaign actions, failures come back as values so the video field
 * can render them inline instead of throwing the builder to its error boundary.
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
    message: "The upload could not be started. Try again.",
    fieldErrors: {},
  };
}

/** Signs a short-lived S3 policy for exactly this one file. */
export async function createVideoUploadTicketAction(
  input: VideoUploadRequest,
): Promise<ActionResult<VideoUploadTicket>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    return { ok: true, data: await createVideoUploadTicket(input) };
  } catch (error) {
    return toFailure(error);
  }
}

/**
 * Confirms the object reached the bucket, and returns the URL to save.
 *
 * S3 answers the browser directly, so this is the only point at which the
 * server learns the upload happened - without it the builder would be storing
 * a URL on the strength of a client-side promise.
 */
export async function completeVideoUploadAction(
  key: string,
): Promise<ActionResult<VideoUploadResult>> {
  if (!(await requireSession())) return UNAUTHENTICATED;

  try {
    return { ok: true, data: await completeVideoUpload(key) };
  } catch (error) {
    return toFailure(error);
  }
}
