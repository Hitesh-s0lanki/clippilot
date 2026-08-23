import { formatCount } from "@/lib/format";

export interface AdsHeaderProps {
  total: number;
}

/**
 * The library's title block.
 *
 * The count sits beside the heading rather than under a paragraph, because it
 * is the one piece of information on this block that changes - and the
 * paragraph beneath it used to restate the heading before explaining the
 * "there" fallback at length. The cards demonstrate that fallback; a visitor
 * does not need it described first.
 */
export function AdsHeader({ total }: AdsHeaderProps) {
  return (
    <header>
      <p className="text-sm font-medium text-primary">Ads library</p>
      <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h1 className="font-heading text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
          Live right now
        </h1>
        <p className="text-sm text-muted-foreground">
          <span className="tabular-nums">{formatCount(total)}</span>{" "}
          {total === 1 ? "campaign" : "campaigns"}
        </p>
      </div>
      <p className="mt-3 max-w-2xl leading-relaxed text-pretty text-muted-foreground">
        Open one to watch and answer it the way a recipient would. No customer is named here.
      </p>
    </header>
  );
}
