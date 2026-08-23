"use client";

import { UploadCloudIcon } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { UploadConfig } from "@/types/upload";

import { useVideoUpload } from "../_hooks/use-video-upload";
import { VideoUploadProgress } from "./video-upload-progress";

export interface VideoUploadFieldProps {
  config: UploadConfig;
  /** Called with the stored URL once S3 has confirmed the object. */
  onUploaded: (url: string) => void;
  disabled?: boolean;
}

/**
 * Drop a video here, or pick one - it lands in S3 and fills the URL field.
 *
 * Renders nothing but a hint when the backend has no bucket configured: an
 * uploader that can only fail is worse than the pasted-URL field beneath it,
 * which keeps working with or without AWS.
 *
 * Drag and drop is the convenience, not the interface. The button beneath it
 * is the accessible path - a drop zone alone is unreachable by keyboard - and
 * the file input stays in the DOM so assistive tech sees a real control.
 */
export function VideoUploadField({ config, onUploaded, disabled }: VideoUploadFieldProps) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const upload = useVideoUpload({ config, onUploaded });

  if (!config.enabled) {
    return (
      <p className="text-xs leading-relaxed text-muted-foreground">
        Uploads are switched off on this server - set <code>S3_BUCKET</code> in the backend
        environment to enable them. Paste a public video URL below instead.
      </p>
    );
  }

  const blocked = disabled || upload.busy;

  function accept(files: FileList | null) {
    const file = files?.[0];
    if (file && !blocked) upload.upload(file);
  }

  if (upload.busy || upload.phase === "done") {
    return <VideoUploadProgress upload={upload} />;
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!blocked) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          accept(event.dataTransfer.files);
        }}
        className={cn(
          "flex flex-col items-center gap-2 rounded-lg border border-dashed border-border px-4 py-5 text-center transition-colors",
          dragging && "border-primary bg-primary/5",
          blocked && "opacity-60",
        )}
      >
        <UploadCloudIcon aria-hidden className="size-5 text-muted-foreground" />

        <p className="text-sm text-foreground">
          Drop a video here, or{" "}
          <Button
            type="button"
            variant="link"
            size="xs"
            className="h-auto p-0 align-baseline"
            disabled={blocked}
            onClick={() => input.current?.click()}
          >
            choose a file
          </Button>
        </p>

        <p className="text-xs text-muted-foreground">
          MP4, WebM or MOV{config.max_bytes > 0 ? ` · up to ${formatBytes(config.max_bytes)}` : ""}
        </p>

        <input
          ref={input}
          type="file"
          className="sr-only"
          tabIndex={-1}
          accept={upload.accept}
          disabled={blocked}
          onChange={(event) => {
            accept(event.target.files);
            // Cleared so re-picking the same file after a failure still fires.
            event.target.value = "";
          }}
        />
      </div>

      {upload.error ? (
        <p role="alert" className="text-sm font-medium text-destructive">
          {upload.error}
        </p>
      ) : null}
    </div>
  );
}
