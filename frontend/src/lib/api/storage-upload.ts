import type { VideoUploadTicket } from "@/types/upload";

import { ApiError } from "./errors";

/**
 * The browser's leg of the upload: the file, straight to S3.
 *
 * `XMLHttpRequest` rather than `fetch`, for one reason - progress. A browser
 * `fetch` still cannot report how much of a request body it has sent, and a
 * 200 MB upload with no progress bar reads as a frozen page. This is the one
 * place in the app that does not go through `./client`, because it does not
 * talk to the ClipPilot API at all.
 */

export interface UploadToStorageOptions {
  ticket: VideoUploadTicket;
  file: File;
  /** Fraction in `0..1`. Called only while the length is computable. */
  onProgress?: (progress: number) => void;
  signal?: AbortSignal;
}

/** S3 returns XML, so the failing condition is dug out of that rather than JSON. */
function s3Error(status: number, body: string): ApiError {
  const code = /<Code>([^<]+)<\/Code>/.exec(body)?.[1] ?? "";

  if (code === "EntityTooLarge") {
    return new ApiError(413, "UPLOAD_TOO_LARGE", "That video is over the size limit.");
  }
  if (code === "AccessDenied" || code === "ExpiredToken") {
    return new ApiError(
      403,
      "UPLOAD_EXPIRED",
      "The upload permission expired before the file finished. Try again.",
    );
  }
  return new ApiError(
    status,
    code || "UPLOAD_FAILED",
    "The video could not be uploaded to storage. Try again.",
  );
}

/**
 * POSTs `file` to S3 under the signed policy in `ticket`.
 *
 * Resolves with the object key on success and throws an {@link ApiError}
 * otherwise, so callers handle it exactly like any other failed request.
 */
export function uploadFileToStorage({
  ticket,
  file,
  onProgress,
  signal,
}: UploadToStorageOptions): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const form = new FormData();
    // Order is part of the contract: S3 ignores every field that arrives
    // after the file, so the signed policy fields have to be appended first.
    for (const [name, value] of Object.entries(ticket.fields)) {
      form.append(name, value);
    }
    form.append("file", file);

    const request = new XMLHttpRequest();
    request.open("POST", ticket.upload_url, true);

    const abort = () => request.abort();
    signal?.addEventListener("abort", abort, { once: true });
    const cleanUp = () => signal?.removeEventListener("abort", abort);

    request.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) {
        onProgress?.(event.loaded / event.total);
      }
    };

    request.onload = () => {
      cleanUp();
      // A presigned POST answers 204 by default, 201 when a success_action is
      // signed into the policy. Anything else carries an XML explanation.
      if (request.status >= 200 && request.status < 300) {
        onProgress?.(1);
        resolve(ticket.key);
      } else {
        reject(s3Error(request.status, request.responseText || ""));
      }
    };

    request.onerror = () => {
      cleanUp();
      // Almost always the bucket's CORS rules: a cross-origin POST that the
      // bucket does not allow fails here with no status to report.
      reject(
        new ApiError(
          0,
          "UPLOAD_NETWORK_ERROR",
          "Could not reach the storage bucket. Check your connection and try again.",
        ),
      );
    };

    request.ontimeout = () => {
      cleanUp();
      reject(new ApiError(0, "UPLOAD_TIMEOUT", "The upload timed out. Try again."));
    };

    request.onabort = () => {
      cleanUp();
      reject(new ApiError(0, "UPLOAD_CANCELLED", "The upload was cancelled."));
    };

    request.send(form);
  });
}
