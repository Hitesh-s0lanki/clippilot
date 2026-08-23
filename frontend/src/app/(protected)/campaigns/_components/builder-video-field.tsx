"use client";

import { WandSparklesIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { UploadConfig } from "@/types/upload";

import type { AdForm } from "../_hooks/use-ad-form";
import { BuilderField } from "./builder-field";
import { VideoUploadField } from "./video-upload-field";

export interface BuilderVideoFieldProps {
  form: AdForm;
  uploads: UploadConfig;
}

/**
 * A publicly reachable sample, for filling the field without hunting for one.
 *
 * The brief allows any public MP4 and explicitly does not ask for video
 * processing, so the fastest path to a working end-to-end demo is a button.
 */
const SAMPLE = {
  video: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
  poster:
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerJoyrides.jpg",
};

/**
 * Where the video comes from: uploaded to S3, pasted, or the sample.
 *
 * All three write the same field. An upload is the convenient path and a URL
 * is the portable one - a customer with the file already on their own CDN
 * should not have to re-upload it through us to use it.
 */
export function BuilderVideoField({ form, uploads }: BuilderVideoFieldProps) {
  const { values, errors, setField, revalidate } = form;

  return (
    <BuilderField
      field="video_url"
      label="Video"
      required
      error={errors["video_url"]}
      hint="Upload a file, or paste a public https link ending in .mp4, .webm or .mov."
    >
      {(control) => (
        <div className="space-y-3">
          <VideoUploadField
            config={uploads}
            disabled={form.pending}
            onUploaded={(url) => {
              setField("video_url", url);
              // Clears the "required to publish" error the moment it is met,
              // rather than leaving it up until the next submit.
              revalidate();
            }}
          />

          <div className="space-y-2">
            <Input
              {...control}
              type="url"
              className="h-9"
              value={values.video_url}
              placeholder="https://cdn.example.com/clips/sip-nudge.mp4"
              onChange={(event) => setField("video_url", event.target.value)}
              onBlur={revalidate}
            />
            <Button
              type="button"
              variant="outline"
              size="xs"
              onClick={() => {
                setField("video_url", SAMPLE.video);
                setField("poster_url", SAMPLE.poster);
              }}
            >
              <WandSparklesIcon data-icon="inline-start" />
              Use a sample video
            </Button>
          </div>
        </div>
      )}
    </BuilderField>
  );
}
