"use client";

import { CheckCircle2Icon, Loader2Icon, RotateCcwIcon, XIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { VideoUpload } from "../_hooks/use-video-upload";

export interface VideoUploadProgressProps {
  upload: VideoUpload;
}

/** What each phase is called while the user waits on it. */
const PHASE_LABEL: Record<string, string> = {
  preparing: "Preparing the upload…",
  uploading: "Uploading",
  finalising: "Checking the file arrived…",
  done: "Uploaded",
};

/**
 * The live state of one upload: what it is doing, how far in, and a way out.
 *
 * `role="progressbar"` with real ARIA values rather than a bare animated div -
 * a screen reader user waiting on a 200 MB upload needs the number, not the
 * animation. Cancel stays reachable throughout, because the alternative to a
 * cancel button on a slow upload is reloading the page and losing the form,
 * and a finished upload turns it into Replace - picking the wrong video is a
 * mistake that should cost one click, not a reload.
 */
export function VideoUploadProgress({ upload }: VideoUploadProgressProps) {
  const percent = Math.round(upload.progress * 100);
  const done = upload.phase === "done";
  const label = PHASE_LABEL[upload.phase] ?? "Working…";

  return (
    <div className="space-y-2 rounded-lg border border-border bg-muted/40 p-3">
      <div className="flex items-center gap-2 text-sm">
        {done ? (
          <CheckCircle2Icon aria-hidden className="size-4 shrink-0 text-success" />
        ) : (
          <Loader2Icon aria-hidden className="size-4 shrink-0 animate-spin text-muted-foreground" />
        )}

        <span className="min-w-0 flex-1 truncate font-medium text-foreground">
          {upload.filename}
        </span>

        <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
          {upload.phase === "uploading" ? `${percent}%` : label}
        </span>

        {done ? (
          <Button type="button" variant="ghost" size="xs" onClick={upload.reset}>
            <RotateCcwIcon data-icon="inline-start" aria-hidden />
            Replace
          </Button>
        ) : (
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            aria-label={`Cancel uploading ${upload.filename}`}
            onClick={upload.cancel}
          >
            <XIcon aria-hidden />
          </Button>
        )}
      </div>

      <div
        role="progressbar"
        aria-label={`${label} ${upload.filename ?? ""}`.trim()}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          style={{ width: `${Math.max(percent, 2)}%` }}
          className={cn(
            "h-full rounded-full transition-[width] duration-200 ease-out",
            done ? "bg-success" : "bg-primary",
          )}
        />
      </div>
    </div>
  );
}
