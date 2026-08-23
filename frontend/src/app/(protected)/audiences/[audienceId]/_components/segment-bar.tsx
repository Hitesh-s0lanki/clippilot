import { formatCount, formatRate } from "@/lib/format";
import type { SegmentBucket } from "@/types/audience";
import { segmentLabel } from "@/types/audience";

export interface SegmentBarProps {
  bucket: SegmentBucket;
  /** The biggest count in this breakdown, so bars are relative to the leader. */
  peak: number;
  /** Where clicking filters the member table to this slice. */
  href: string;
  active?: boolean;
}

/**
 * One row of a breakdown: a label, a proportional bar, a count.
 *
 * Scaled against the largest bucket rather than the whole audience, so a list
 * spread over ten cities still draws a readable chart instead of ten stubs.
 * The share is spelled out in text beside it, because the bar is a comparison
 * and the number is the fact.
 *
 * A link, not a chart: the point of seeing that 22 people are in Mumbai is
 * being able to go and look at them.
 */
export function SegmentBar({ bucket, peak, href, active = false }: SegmentBarProps) {
  const width = peak > 0 ? Math.max(2, Math.round((bucket.count / peak) * 100)) : 0;

  return (
    <li>
      <a
        href={href}
        aria-current={active ? "true" : undefined}
        className="group grid grid-cols-[minmax(0,7rem)_1fr_auto] items-center gap-3 rounded-md px-1 py-1 hover:bg-accent focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
      >
        <span className="truncate text-sm text-muted-foreground group-hover:text-foreground">
          {segmentLabel(bucket.key)}
        </span>
        <span aria-hidden className="h-2 overflow-hidden rounded-full bg-muted">
          <span
            className={active ? "block h-full bg-primary" : "block h-full bg-primary/60"}
            style={{ width: `${width}%` }}
          />
        </span>
        <span className="text-sm font-medium tabular-nums">
          {formatCount(bucket.count)}
          <span className="ml-1.5 text-xs font-normal text-muted-foreground">
            {formatRate(bucket.share)}
          </span>
        </span>
      </a>
    </li>
  );
}
