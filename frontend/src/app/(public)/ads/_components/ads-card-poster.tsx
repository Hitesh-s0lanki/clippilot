import { PlayIcon } from "lucide-react";

import { AdsPosterImage } from "./ads-poster-image";

export interface AdsCardPosterProps {
  posterUrl: string | null;
  /** Rendered as a corner chip when the campaign declares one. */
  duration: string | null;
}

/**
 * The card's 16:9 cover.
 *
 * Drawn at a fixed aspect ratio over a gradient whether or not there is a
 * poster, so the grid never reflows once images load and a campaign without
 * one still lines up with its neighbours.
 *
 * The image is split into `AdsPosterImage` because a poster URL that no longer
 * resolves has to be caught in the browser, which needs a client leaf. This
 * half stays a Server Component so only the `<img>` crosses the boundary.
 */
export function AdsCardPoster({ posterUrl, duration }: AdsCardPosterProps) {
  return (
    <div className="relative aspect-video overflow-hidden bg-gradient-to-br from-primary/25 via-primary/10 to-chart-2/20">
      {posterUrl ? <AdsPosterImage src={posterUrl} /> : null}

      <span className="absolute inset-0 grid place-items-center">
        <span className="grid size-11 place-items-center rounded-full bg-background/85 shadow-sm backdrop-blur transition-transform group-hover/ad:scale-110">
          <PlayIcon aria-hidden className="size-4 translate-x-px fill-primary text-primary" />
        </span>
      </span>

      {duration ? (
        <span className="absolute right-2 bottom-2 rounded-md bg-background/80 px-1.5 py-0.5 font-mono text-[0.6875rem] text-muted-foreground backdrop-blur">
          {duration}
        </span>
      ) : null}
    </div>
  );
}
