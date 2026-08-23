import { EyeIcon, MousePointerClickIcon, PlayIcon, PercentIcon } from "lucide-react";

import { MetricTile } from "../../../../_components/metric-tile";
import { formatCount, formatRate } from "@/lib/format";
import type { CampaignAnalytics } from "@/types/analytics";

export interface AnalyticsMetricGridProps {
  analytics: CampaignAnalytics;
}

/**
 * The brief's supporting metrics.
 *
 * `interaction_rate` is served as `0` when there are no views, so nothing here
 * divides and nothing renders `NaN` - a campaign nobody has opened reads as a
 * row of zeros, which is the truth about it.
 */
export function AnalyticsMetricGrid({ analytics }: AnalyticsMetricGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <MetricTile label="Total views" value={formatCount(analytics.views)} icon={PlayIcon} />
      <MetricTile
        label="Unique viewers"
        value={formatCount(analytics.unique_viewers)}
        icon={EyeIcon}
      />
      <MetricTile
        label="Interactions"
        value={formatCount(analytics.interactions)}
        icon={MousePointerClickIcon}
      />
      <MetricTile
        label="Interaction rate"
        value={formatRate(analytics.interaction_rate)}
        icon={PercentIcon}
        hint="Responses ÷ views"
      />
    </div>
  );
}
