import { cn } from "@/lib/utils";
import { INTENT_LABELS } from "@/lib/campaign-labels";
import { formatCount, formatRate } from "@/lib/format";
import type { OptionBreakdown } from "@/types/analytics";

import { ResponseSplitBar } from "./response-split-bar";

export interface ResponseBreakdownProps {
  options: OptionBreakdown[];
  interactions: number;
}

const SERIES = ["bg-chart-1", "bg-chart-2", "bg-chart-3", "bg-chart-4", "bg-chart-5"];

/**
 * Clicks per option, and the split between them.
 *
 * Every option gets a row, including the ones nobody clicked: a zero is a
 * finding, and a chart with a missing bar reads as a bug. The percentage is
 * never shown alone - "50%" of two responses and of two thousand are different
 * facts, so the raw count sits beside it.
 */
export function ResponseBreakdown({ options, interactions }: ResponseBreakdownProps) {
  if (options.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        This campaign has no response options configured yet.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <ResponseSplitBar options={options} interactions={interactions} />

      <ul className="divide-y divide-border">
        {options.map((option, index) => (
          <li key={option.option_id} className="flex items-center gap-3 py-3">
            <span
              aria-hidden
              className={cn("size-2.5 shrink-0 rounded-sm", SERIES[index % SERIES.length])}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{option.label}</p>
              <p className="text-xs text-muted-foreground">
                Option {option.position} · {INTENT_LABELS[option.intent]} intent
              </p>
            </div>
            <div className="text-right">
              <p className="font-heading text-lg font-semibold tabular-nums">
                {formatRate(option.share)}
              </p>
              <p className="text-xs text-muted-foreground tabular-nums">
                {formatCount(option.clicks)} {option.clicks === 1 ? "click" : "clicks"}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
