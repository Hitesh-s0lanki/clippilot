import type { SegmentBucket } from "@/types/audience";

import { SegmentBar } from "./segment-bar";

export interface SegmentBreakdownProps {
  title: string;
  /** Why this cut of the list is worth seeing, in one line. */
  hint?: string;
  buckets: SegmentBucket[];
  /** Builds the filter link for one bucket. */
  hrefFor: (key: string) => string;
  /** The bucket currently filtering the table, if any. */
  activeKey?: string;
  /** Message when nothing in the list carries this field at all. */
  emptyLabel: string;
}

/** One cut of the audience - by age, by gender, by city, by country. */
export function SegmentBreakdown({
  title,
  hint,
  buckets,
  hrefFor,
  activeKey,
  emptyLabel,
}: SegmentBreakdownProps) {
  const peak = buckets.reduce((highest, bucket) => Math.max(highest, bucket.count), 0);

  return (
    <section className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
      <h3 className="font-heading text-sm font-semibold tracking-tight">{title}</h3>
      {hint ? <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p> : null}

      {buckets.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">{emptyLabel}</p>
      ) : (
        <ul className="mt-4 space-y-1.5">
          {buckets.map((bucket) => (
            <SegmentBar
              key={bucket.key}
              bucket={bucket}
              peak={peak}
              href={hrefFor(bucket.key)}
              active={bucket.key === activeKey}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
