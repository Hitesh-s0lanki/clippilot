import { MousePointerClickIcon, PlayIcon } from "lucide-react";

import { formatCount } from "@/lib/format";
import { leadMetric } from "@/lib/campaign-labels";
import type { CampaignMetrics, CampaignObjective } from "@/types/campaign";

export interface CampaignCardMetricsProps {
  objective: CampaignObjective;
  metrics: CampaignMetrics;
}

/**
 * The card's numbers: the objective's headline metric, large, with the brief's
 * views and interactions counts beneath it.
 *
 * A campaign that nobody has opened shows `0`, never a blank - `0 views` is a
 * fact about the campaign, and an empty slot reads as a loading bug. The views
 * chip drops out when the objective already leads with views, so an awareness
 * campaign does not print the same number twice.
 */
export function CampaignCardMetrics({ objective, metrics }: CampaignCardMetricsProps) {
  const lead = leadMetric(objective, metrics);
  const leadsWithViews = lead.label === "Total views";

  return (
    <div className="flex items-end justify-between gap-4 border-t border-border pt-3">
      <div>
        <p className="text-xs text-muted-foreground">{lead.label}</p>
        <p className="font-heading text-2xl font-semibold tracking-tight tabular-nums">
          {lead.value}
        </p>
      </div>
      <dl className="flex items-center gap-4 text-sm">
        {leadsWithViews ? null : (
          <div className="flex items-center gap-1.5">
            <PlayIcon aria-hidden className="size-3.5 text-muted-foreground" />
            <dt className="sr-only">Views</dt>
            <dd className="tabular-nums">{formatCount(metrics.views)}</dd>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <MousePointerClickIcon aria-hidden className="size-3.5 text-muted-foreground" />
          <dt className="sr-only">Interactions</dt>
          <dd className="tabular-nums">{formatCount(metrics.interactions)}</dd>
        </div>
      </dl>
    </div>
  );
}
