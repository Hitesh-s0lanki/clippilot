import { UsersIcon } from "lucide-react";
import Link from "next/link";

import { formatCount, formatDate } from "@/lib/format";
import type { AudienceSummary } from "@/types/audience";

export interface AudienceCardProps {
  audience: AudienceSummary;
}

/**
 * One list, as a card.
 *
 * The whole card is the link rather than a "View" button in the corner: the
 * card has one destination, and a 200px target beats a 60px one on a phone.
 */
export function AudienceCard({ audience }: AudienceCardProps) {
  return (
    <Link
      href={`/audiences/${audience.id}`}
      className="group flex flex-col gap-3 rounded-xl bg-card p-5 ring-1 ring-foreground/10 transition-shadow hover:shadow-md focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-heading font-semibold tracking-tight group-hover:underline">
          {audience.name}
        </h2>
        <span className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-muted px-2 py-1 text-xs font-medium tabular-nums">
          <UsersIcon aria-hidden className="size-3.5" />
          {formatCount(audience.member_count)}
        </span>
      </div>

      {audience.description ? (
        <p className="line-clamp-2 text-sm text-pretty text-muted-foreground">
          {audience.description}
        </p>
      ) : null}

      <p className="mt-auto text-xs text-muted-foreground">
        {audience.campaign_count === 0
          ? "Not used by a campaign yet"
          : `Targeted by ${formatCount(audience.campaign_count)} campaign${audience.campaign_count === 1 ? "" : "s"}`}
        {" · "}
        Created {formatDate(audience.created_at)}
      </p>
    </Link>
  );
}
