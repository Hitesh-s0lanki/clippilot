import { MousePointerClickIcon, PlayIcon, RadioIcon, VideoIcon } from "lucide-react";

import { MetricTile } from "../../_components/metric-tile";
import { listCampaigns } from "@/lib/api/campaigns";
import { formatCount, formatRate } from "@/lib/format";

/** The backend caps a page at 100; the strip says so rather than under-reporting. */
const SUMMARY_LIMIT = 100;

/**
 * The portfolio strip above the list.
 *
 * A second, unfiltered request on purpose: the strip answers "how is
 * everything doing", which must not change when the list below is filtered to
 * one status. It is a separate async component so a `Suspense` boundary can
 * stream it - the campaign list does not wait on this number.
 */
export async function DashboardSummary() {
  const page = await listCampaigns({ limit: SUMMARY_LIMIT, includeArchived: false });

  const live = page.items.filter((campaign) => campaign.effective_status === "ACTIVE").length;
  const views = page.items.reduce((total, campaign) => total + campaign.metrics.views, 0);
  const interactions = page.items.reduce(
    (total, campaign) => total + campaign.metrics.interactions,
    0,
  );
  const rate = views ? interactions / views : 0;
  const partial = page.total > SUMMARY_LIMIT;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <MetricTile
        label="Campaigns"
        value={formatCount(page.total)}
        icon={VideoIcon}
        hint={partial ? `Totals below cover the most recent ${SUMMARY_LIMIT}` : undefined}
      />
      <MetricTile label="Live now" value={formatCount(live)} icon={RadioIcon} />
      <MetricTile label="Views" value={formatCount(views)} icon={PlayIcon} />
      <MetricTile
        label="Interactions"
        value={formatCount(interactions)}
        icon={MousePointerClickIcon}
        hint={`${formatRate(rate)} of views responded`}
      />
    </div>
  );
}
