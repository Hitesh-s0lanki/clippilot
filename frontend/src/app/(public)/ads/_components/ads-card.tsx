import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { OBJECTIVE_LABELS, SPECIAL_CATEGORY_CHIPS } from "@/lib/campaign-labels";
import { formatDate, formatDuration } from "@/lib/format";
import type { PublicCampaignCard } from "@/types/public";

import { AdsCardPoster } from "./ads-card-poster";

export interface AdsCardProps {
  ad: PublicCampaignCard;
}

/**
 * One live ad in the library.
 *
 * The link is on the heading and stretched over the card with a pseudo-element,
 * rather than wrapped around everything. Both give one big target; only this
 * one gives the link a usable name. Wrapping the card made its accessible name
 * the objective, the compliance chip, the headline, the message and both
 * option labels read out as a single link.
 *
 * The copy shown is the ad's own, resolved by the server with no recipient
 * bound - which is why it reads "Hi there" and never names a customer. The
 * link carries `ad_id`, so a campaign with several creatives opens the one
 * this card is actually showing.
 */
export function AdsCard({ ad }: AdsCardProps) {
  const category = SPECIAL_CATEGORY_CHIPS[ad.special_category];

  return (
    <li className="group/ad relative flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-colors hover:border-primary/40 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
      <AdsCardPoster
        posterUrl={ad.poster_url}
        duration={ad.video_duration_seconds ? formatDuration(ad.video_duration_seconds) : null}
      />

      <div className="flex flex-1 flex-col p-5">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="secondary">{OBJECTIVE_LABELS[ad.objective]}</Badge>
          {category ? <Badge variant="warning">{category}</Badge> : null}
        </div>

        <h3 className="mt-3 font-heading font-semibold tracking-tight text-balance">
          <Link
            href={`/preview/${ad.campaign_id}?ad_id=${ad.ad_id}`}
            className="after:absolute after:inset-0 focus-visible:outline-none"
          >
            {ad.headline ?? ad.campaign_name}
          </Link>
        </h3>
        <p className="mt-1.5 line-clamp-3 text-sm leading-relaxed text-pretty text-muted-foreground">
          {ad.preview_message}
        </p>

        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-border pt-4">
          <ul className="flex flex-wrap gap-1.5">
            {ad.option_labels.map((label) => (
              <li
                key={label}
                className="rounded-4xl border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground"
              >
                {label}
              </li>
            ))}
          </ul>
          {ad.published_at ? (
            <p className="ml-auto text-xs text-muted-foreground">
              Live since {formatDate(ad.published_at)}
            </p>
          ) : null}
        </div>
      </div>
    </li>
  );
}
