"use client";

import { PlayIcon } from "lucide-react";
import { useRef, useState } from "react";

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
 *
 * The play overlay is a real button that calls `play()`, not a decoration
 * drawn over the video. Browsers disagree about what a click on the body of a
 * `<video controls>` means - WebKit starts playback, Chrome ignores it - so an
 * overlay that let clicks fall through to the video was a dead button in
 * Chrome, on the largest target the screen has. It covers the whole frame
 * because until playback starts there is nothing else here worth clicking, and
 * it unmounts on the first `play` so the native controls own every later one.
 */
export function PreviewPlayer({
  videoUrl,
  posterUrl,
  captionsUrl,
  title,
  onPlay,
}: PreviewPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [started, setStarted] = useState(false);

  function handlePlay() {
    if (!started) setStarted(true);
    onPlay();
  }

  function start() {
    // `started` is left to the video's own `play` event, so pressing the native
    // control bar hides this overlay too. A rejected promise means the browser
    // refused the gesture; the native controls are still there to try again.
    void videoRef.current?.play().catch(() => {});
  }

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-foreground/90 ring-1 ring-foreground/10">
      <video
        ref={videoRef}
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
        <button
          type="button"
          onClick={start}
          aria-label={`Play ${title}`}
          className="absolute inset-0 flex cursor-pointer items-center justify-center focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <span
            aria-hidden
            className="flex size-16 items-center justify-center rounded-full bg-background/90 shadow-lg transition-transform hover:scale-105"
          >
            <PlayIcon className="ml-1 size-7 text-foreground" />
          </span>
        </button>
      ) : null}
    </div>
  );
}
