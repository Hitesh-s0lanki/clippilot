import type { Metadata } from "next";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCampaignAnalytics } from "@/lib/api/analytics";
import { formatDateTime } from "@/lib/format";

import { loadCampaign } from "../../_lib/load-campaign";
import { AnalyticsEmptyState } from "./_components/analytics-empty-state";
import { AnalyticsHeadline } from "./_components/analytics-headline";
import { AnalyticsMetricGrid } from "./_components/analytics-metric-grid";
import { ResponseBreakdown } from "./_components/response-breakdown";

export const metadata: Metadata = { title: "Analytics" };

export default async function CampaignAnalyticsPage({
  params,
}: PageProps<"/campaigns/[campaignId]/analytics">) {
  const { campaignId } = await params;
  const [campaign, analytics] = await Promise.all([
    loadCampaign(campaignId),
    getCampaignAnalytics(campaignId),
  ]);

  const timezone = campaign.schedule.timezone;
  const hasActivity = analytics.views > 0 || analytics.interactions > 0;

  return (
    <div className="space-y-6">
      <AnalyticsHeadline
        objective={campaign.objective}
        metric={analytics.primary_metric}
        lastActivityAt={analytics.last_activity_at}
        timezone={timezone}
      />

      <AnalyticsMetricGrid analytics={analytics} />

      {hasActivity ? (
        <Card>
          <CardHeader>
            <CardTitle>Response split</CardTitle>
            <CardDescription>
              How the {analytics.interactions} recorded{" "}
              {analytics.interactions === 1 ? "response" : "responses"} divided between the two
              options.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponseBreakdown
              options={analytics.by_option}
              interactions={analytics.interactions}
            />
            {analytics.first_activity_at ? (
              <p className="mt-4 border-t border-border pt-3 text-xs text-muted-foreground">
                First activity {formatDateTime(analytics.first_activity_at, timezone)} · shown in{" "}
                {timezone}
              </p>
            ) : null}
          </CardContent>
        </Card>
      ) : (
        <AnalyticsEmptyState campaignId={campaignId} status={campaign.effective_status} />
      )}
    </div>
  );
}
