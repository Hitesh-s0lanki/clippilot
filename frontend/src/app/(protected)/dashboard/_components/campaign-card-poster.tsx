import { VideoIcon } from "lucide-react";
import Image from "next/image";

export interface CampaignCardPosterProps {
  posterUrl: string | null;
  /** Only for the alt text, so the thumbnail says which campaign it belongs to. */
  campaignName: string;
}

/**
 * The card's 16:9 thumbnail.
 *
 * The box is drawn at a fixed aspect ratio whether or not there is an image,
 * so the row never reflows once the poster loads and a campaign without one
 * still lines up with its neighbours. `unoptimized` because the URL is
 * whatever the campaign owner typed - it is validated for scheme and host by
 * the API, not owned by us, and running it through the image optimiser only
 * adds a way for it to fail.
 */
export function CampaignCardPoster({ posterUrl, campaignName }: CampaignCardPosterProps) {
  return (
    <div className="relative aspect-video w-20 shrink-0 overflow-hidden rounded-lg bg-muted ring-1 ring-foreground/10">
      {posterUrl ? (
        <Image
          src={posterUrl}
          alt={`Poster frame for ${campaignName}`}
          fill
          unoptimized
          sizes="80px"
          className="object-cover"
        />
      ) : (
        <span className="flex size-full items-center justify-center text-muted-foreground">
          <VideoIcon aria-hidden className="size-4" />
        </span>
      )}
    </div>
  );
}
