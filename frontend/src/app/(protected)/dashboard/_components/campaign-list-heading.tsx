import { formatCount } from "@/lib/format";

export interface CampaignListHeadingProps {
  /** Every campaign matching the current filters, not just this page's slice. */
  total: number;
  filtered: boolean;
}

/**
 * The heading above the card grid, with the size of the result set.
 *
 * The heading used to be `sr-only`, which left the grid starting with no
 * announcement of what it was and no answer to "how many are there" until the
 * pagination row - and that row hides itself when everything fits on one page,
 * so on a small account the count was never shown at all.
 *
 * The wording changes under a filter because "All campaigns · 3" next to a
 * search box reads as "you only have three".
 */
export function CampaignListHeading({ total, filtered }: CampaignListHeadingProps) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <h2 id="campaign-list-heading" className="font-heading text-lg font-semibold tracking-tight">
        {filtered ? "Matching campaigns" : "All campaigns"}
      </h2>
      <p className="shrink-0 text-sm text-muted-foreground">
        <span className="tabular-nums">{formatCount(total)}</span>{" "}
        {total === 1 ? "result" : "results"}
      </p>
    </div>
  );
}
