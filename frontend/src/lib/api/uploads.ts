import "server-only";

import type {
  UploadConfig,
  VideoUploadRequest,
  VideoUploadResult,
  VideoUploadTicket,
} from "@/types/upload";

import { api } from "./client";
import { getSessionToken } from "./session";

/**
 * The authenticated upload resource.
 *
 * Server-only, like `./campaigns`: every call carries the Clerk session token,
 * read per request. The browser's own leg of the upload - the one that carries
 * the file - goes to S3, not here, and lives in `./storage-upload`.
 */

/** Disabled is the honest answer when the API cannot be reached. */
const UNAVAILABLE: UploadConfig = {
  enabled: false,
  max_bytes: 0,
  accepted_content_types: [],
};

/**
 * Whether the builder should offer an uploader, and its limits.
 *
 * Never throws: an unreachable API must degrade the video field to "paste a
 * URL" rather than take down the whole builder page with it.
 */
export async function getUploadConfig(): Promise<UploadConfig> {
  try {
    return await api.get<UploadConfig>("/uploads/config", {
      token: await getSessionToken(),
      cache: "no-store",
    });
  } catch {
    return UNAVAILABLE;
  }
}

export async function createVideoUploadTicket(
  input: VideoUploadRequest,
): Promise<VideoUploadTicket> {
  return api.post<VideoUploadTicket>("/uploads/video", {
    body: input,
    token: await getSessionToken(),
  });
}

/** Confirms with S3 that the object exists, and returns the URL to save. */
export async function completeVideoUpload(key: string): Promise<VideoUploadResult> {
  return api.post<VideoUploadResult>("/uploads/video/complete", {
    body: { key },
    token: await getSessionToken(),
    // A HEAD against S3 can be slower than a database read, and failing this
    // step throws away an upload the user has already waited through.
    timeoutMs: 20_000,
  });
}
