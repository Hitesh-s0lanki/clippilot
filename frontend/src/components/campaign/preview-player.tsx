"use client";

import { PlayIcon } from "lucide-react";
import { useState } from "react";

export interface PreviewPlayerProps {
  videoUrl: string;
  posterUrl: string | null;
  captionsUrl: string | null;
  /** Used for the player's accessible name. */
  title: string;
  /** Fires once, when playback actually begins. */
  onPlay: () => void;
}

/**
 * The campaign video.
 *
 * Click to play, never autoplay: a video that starts talking on its own in
 * someone's inbox is the behaviour this product would be judged for. The
 * aspect box is drawn before the video loads so the message and buttons below
 * it do not jump when it does, and `preload="none"` keeps a campaign that is
 * opened and closed from costing the recipient a download.
 */
export function PreviewPlayer({
  videoUrl,
  posterUrl,
  captionsUrl,
  title,
  onPlay,
}: PreviewPlayerProps) {
  const [started, setStarted] = useState(false);

  function handlePlay() {
    if (!started) setStarted(true);
    onPlay();
  }

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-foreground/90 ring-1 ring-foreground/10">
      <video
        controls
        playsInline
        preload="none"
        poster={posterUrl ?? undefined}
        src={videoUrl}
        aria-label={title}
        onPlay={handlePlay}
        className="size-full object-contain"
      >
        {captionsUrl ? (
          <track kind="captions" src={captionsUrl} srcLang="en" label="English" default />
        ) : null}
      </video>

      {!started ? (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0 flex items-center justify-center"
        >
          <span className="flex size-16 items-center justify-center rounded-full bg-background/90 shadow-lg">
            <PlayIcon className="ml-1 size-7 text-foreground" />
          </span>
        </span>
      ) : null}
    </div>
  );
}
