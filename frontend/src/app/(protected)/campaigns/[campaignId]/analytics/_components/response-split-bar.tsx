import { cn } from "@/lib/utils";
import { formatRate } from "@/lib/format";
import type { OptionBreakdown } from "@/types/analytics";

export interface ResponseSplitBarProps {
  options: OptionBreakdown[];
  /** Total responses. `0` renders the empty rail rather than a broken bar. */
  interactions: number;
}

/** Series colours, in the order the options are defined. */
const SERIES = ["bg-chart-1", "bg-chart-2", "bg-chart-3", "bg-chart-4", "bg-chart-5"];

/**
 * The split between the response options, as one 100% stacked bar.
 *
 * A stacked bar rather than a pie: two adjacent angles are hard to compare and
 * harder to label, and the accessible version of a pie is a table anyway. This
 * is `aria-hidden` for exactly that reason - the numbers beneath it are the
 * real content, and reading the bar twice would only be noise.
 */
export function ResponseSplitBar({ options, interactions }: ResponseSplitBarProps) {
  if (interactions === 0) {
    return (
      <div className="h-3 w-full rounded-full bg-muted" aria-hidden>
        <span className="sr-only">No responses yet</span>
      </div>
    );
  }

  return (
    <div aria-hidden className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
      {options.map((option, index) => (
        <span
          key={option.option_id}
          title={`${option.label}: ${formatRate(option.share)}`}
          style={{ width: `${option.share * 100}%` }}
          className={cn("h-full", SERIES[index % SERIES.length])}
        />
      ))}
    </div>
  );
}
