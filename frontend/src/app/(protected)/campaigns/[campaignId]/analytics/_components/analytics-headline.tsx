import { OBJECTIVE_LABELS, formatPrimaryMetric } from "@/lib/campaign-labels";
import { formatDateTime } from "@/lib/format";
import type { CampaignObjective, PrimaryMetric } from "@/types/campaign";

export interface AnalyticsHeadlineProps {
  objective: CampaignObjective;
  metric: PrimaryMetric | null;
  lastActivityAt: string | null;
  timezone: string;
}

/**
 * The one number the objective says matters.
 *
 * An awareness campaign leads with views and a lead-capture campaign with
 * positive intent, the same way an ads manager does - the server picks it, so
 * the screen cannot disagree with the card that linked here. The brief's six
 * metrics stay, as the supporting row beneath.
 */
export function AnalyticsHeadline({
  objective,
  metric,
  lastActivityAt,
  timezone,
}: AnalyticsHeadlineProps) {
  return (
    <div className="rounded-xl bg-primary/5 p-6 ring-1 ring-primary/20">
      <p className="text-sm font-medium text-primary">
        {OBJECTIVE_LABELS[objective]} · {metric?.label ?? "Primary metric"}
      </p>
      <p className="mt-2 font-heading text-4xl font-semibold tracking-tight tabular-nums sm:text-5xl">
        {metric ? formatPrimaryMetric(metric) : "—"}
      </p>
      <p className="mt-2 text-sm text-muted-foreground">
        {lastActivityAt
          ? `Last response ${formatDateTime(lastActivityAt, timezone)}`
          : "No activity recorded yet."}
      </p>
    </div>
  );
}
