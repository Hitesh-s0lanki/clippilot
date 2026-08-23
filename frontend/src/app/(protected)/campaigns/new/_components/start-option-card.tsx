import type { LucideIcon } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";

export interface StartOptionCardProps {
  Icon: LucideIcon;
  title: string;
  description: string;
  /** What this route actually does, in three short lines. */
  points: string[];
  href: string;
  badge?: string;
  /** When set, the card is inert and says why instead of linking. */
  unavailable?: string;
}

/**
 * One way to start a campaign.
 *
 * The whole card is the target, via a stretched link on the heading rather
 * than an anchor wrapped around everything: both give one big hit area, only
 * this one gives the link a usable accessible name instead of reading out the
 * title, the description and every bullet as a single link.
 */
export function StartOptionCard({
  Icon,
  title,
  description,
  points,
  href,
  badge,
  unavailable,
}: StartOptionCardProps) {
  return (
    <li
      className={
        unavailable
          ? "flex flex-col rounded-xl border border-border bg-card p-6 opacity-60"
          : "group relative flex flex-col rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/40 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50"
      }
    >
      <div className="flex items-center gap-2">
        <Icon aria-hidden className="size-5 text-primary" />
        {badge ? <Badge variant="secondary">{badge}</Badge> : null}
      </div>

      <h2 className="mt-3 font-heading text-lg font-semibold tracking-tight">
        {unavailable ? (
          title
        ) : (
          <Link href={href} className="after:absolute after:inset-0 focus-visible:outline-none">
            {title}
          </Link>
        )}
      </h2>

      <p className="mt-1 text-sm text-pretty text-muted-foreground">{description}</p>

      <ul className="mt-4 space-y-1.5 text-sm text-muted-foreground">
        {points.map((point) => (
          <li key={point} className="flex items-start gap-2">
            <span aria-hidden className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/50" />
            {point}
          </li>
        ))}
      </ul>

      {unavailable ? (
        <p className="mt-4 border-t border-border pt-3 text-xs text-muted-foreground">
          {unavailable}
        </p>
      ) : null}
    </li>
  );
}
