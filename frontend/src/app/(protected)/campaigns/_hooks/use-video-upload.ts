"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  completeVideoUploadAction,
  createVideoUploadTicketAction,
} from "@/lib/actions/upload-actions";
import { uploadFileToStorage } from "@/lib/api/storage-upload";
import { isApiError } from "@/lib/api/errors";
import { formatBytes } from "@/lib/format";
import type { UploadConfig } from "@/types/upload";

/** Sign, send, confirm. The UI names each step so a stall is legible. */
export type VideoUploadPhase = "idle" | "preparing" | "uploading" | "finalising" | "done" | "error";

export interface VideoUploadState {
  phase: VideoUploadPhase;
  /** Fraction in `0..1`, meaningful during `uploading`. */
  progress: number;
  filename: string | null;
  error: string | null;
  busy: boolean;
}

export interface UseVideoUploadOptions {
  config: UploadConfig;
  /** Handed the final public URL, once S3 has confirmed the object exists. */
  onUploaded: (url: string) => void;
}

export interface VideoUpload extends VideoUploadState {
  /** File types for the input's `accept`, e.g. `video/mp4,video/webm`. */
  accept: string;
  upload: (file: File) => void;
  cancel: () => void;
  reset: () => void;
}

const IDLE: VideoUploadState = {
  phase: "idle",
  progress: 0,
  filename: null,
  error: null,
  busy: false,
};

/**
 * Drives one video from a file input to a saved URL.
 *
 * Three steps, because the bytes go to S3 and not to the API: ask the backend
 * to sign a policy, POST the file to the bucket, then have the backend confirm
 * the object landed. Only that last step produces the URL the form saves - a
 * finished XHR is the browser's word for it, and the preview page is where a
 * wrong answer would show up.
 *
 * Type and size are checked here before any network call, so the common
 * mistakes cost nothing; both are re-checked on the server and, for size, by
 * S3 itself under the signed policy.
 */
export function useVideoUpload({ config, onUploaded }: UseVideoUploadOptions): VideoUpload {
  const [state, setState] = useState<VideoUploadState>(IDLE);
  const controller = useRef<AbortController | null>(null);
  // Incremented per attempt, so a cancelled or superseded run cannot write its
  // result over a newer one after the fact.
  const run = useRef(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
    };
  }, []);

  const cancel = useCallback(() => {
    run.current += 1;
    controller.current?.abort();
    controller.current = null;
    setState(IDLE);
  }, []);

  const reset = useCallback(() => setState(IDLE), []);

  const upload = useCallback(
    (file: File) => {
      const attempt = (run.current += 1);
      const current = () => mounted.current && run.current === attempt;

      const fail = (message: string) => {
        if (current()) {
          setState({
            phase: "error",
            progress: 0,
            filename: file.name,
            error: message,
            busy: false,
          });
        }
      };

      const type = file.type.toLowerCase();
      if (
        config.accepted_content_types.length > 0 &&
        !config.accepted_content_types.includes(type)
      ) {
        fail(`${file.name} is not a video this accepts. Use an MP4, WebM or MOV file.`);
        return;
      }
      if (config.max_bytes > 0 && file.size > config.max_bytes) {
        fail(
          `${file.name} is ${formatBytes(file.size)}. The limit is ${formatBytes(config.max_bytes)}.`,
        );
        return;
      }

      const abort = new AbortController();
      controller.current = abort;
      setState({ phase: "preparing", progress: 0, filename: file.name, error: null, busy: true });

      void (async () => {
        try {
          const ticket = await createVideoUploadTicketAction({
            filename: file.name,
            content_type: type,
            size_bytes: file.size,
          });
          if (!current()) return;
          if (!ticket.ok) {
            fail(ticket.message);
            return;
          }

          setState((previous) => ({ ...previous, phase: "uploading" }));

          const key = await uploadFileToStorage({
            ticket: ticket.data,
            file,
            signal: abort.signal,
            onProgress: (progress) => {
              if (current()) setState((previous) => ({ ...previous, progress }));
            },
          });
          if (!current()) return;

          setState((previous) => ({ ...previous, phase: "finalising", progress: 1 }));

          const confirmed = await completeVideoUploadAction(key);
          if (!current()) return;
          if (!confirmed.ok) {
            fail(confirmed.message);
            return;
          }

          setState({
            phase: "done",
            progress: 1,
            filename: file.name,
            error: null,
            busy: false,
          });
          onUploaded(confirmed.data.video_url);
        } catch (error) {
          if (isApiError(error) && error.code === "UPLOAD_CANCELLED") return;
          fail(isApiError(error) ? error.message : "The upload failed. Try again, or paste a URL.");
        } finally {
          if (controller.current === abort) controller.current = null;
        }
      })();
    },
    [config.accepted_content_types, config.max_bytes, onUploaded],
  );

  return {
    ...state,
    accept: config.accepted_content_types.join(","),
    upload,
    cancel,
    reset,
  };
}
