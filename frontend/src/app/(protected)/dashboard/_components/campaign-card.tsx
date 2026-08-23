import { CalendarIcon, PencilIcon, PlayCircleIcon, UsersIcon } from "lucide-react";
import Link from "next/link";

import { CampaignActionsMenu } from "../../_components/campaign-actions-menu";
import { CampaignStatusBadge } from "../../_components/campaign-status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { OBJECTIVE_LABELS, formatMemberCount } from "@/lib/campaign-labels";
import { formatDate } from "@/lib/format";
import type { CampaignSummary } from "@/types/campaign";

import { CampaignCardMetrics } from "./campaign-card-metrics";
import { CampaignCardPoster } from "./campaign-card-poster";

export interface CampaignCardProps {
  campaign: CampaignSummary;
}

/**
 * One campaign on the dashboard.
 *
 * A card rather than a table row: a status badge, an objective, a recipient
 * count and two metrics are what a column set handles worst on a phone. The
 * whole title is the link to the builder, so the primary target is a full line
 * of text rather than a 16px icon.
 */
export function CampaignCard({ campaign }: CampaignCardProps) {
  const { id, name, objective, badge, effective_status, metrics } = campaign;

  return (
    <Card className="transition-shadow hover:ring-foreground/20">
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <CampaignCardPoster posterUrl={campaign.poster_url} campaignName={name} />

          <div className="min-w-0 flex-1">
            <h3 className="font-heading leading-snug font-medium">
              <Link
                href={`/campaigns/${id}/edit`}
                className="line-clamp-2 rounded transition-colors hover:text-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                {name}
              </Link>
            </h3>
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              {OBJECTIVE_LABELS[objective]} · {badge}
            </p>
          </div>

          <CampaignStatusBadge status={effective_status} />
        </div>

        <dl className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <CalendarIcon aria-hidden className="size-3.5" />
            <dt className="sr-only">Created</dt>
            <dd>{formatDate(campaign.created_at)}</dd>
          </div>
          <div className="flex items-center gap-1.5">
            <UsersIcon aria-hidden className="size-3.5" />
            <dt className="sr-only">Audience</dt>
            <dd>{formatMemberCount(campaign.audience_size)}</dd>
          </div>
          {metrics.last_activity_at ? (
            <div className="flex items-center gap-1.5">
              <dt className="sr-only">Last activity</dt>
              <dd>
                <Badge variant="ghost" className="text-muted-foreground">
                  Last activity {formatDate(metrics.last_activity_at)}
                </Badge>
              </dd>
            </div>
          ) : null}
        </dl>

        <CampaignCardMetrics objective={objective} metrics={metrics} />

        <div className="flex items-center gap-2 border-t border-border pt-3">
          <Button asChild variant="outline" size="sm">
            <Link href={`/campaigns/${id}/preview`}>
              <PlayCircleIcon data-icon="inline-start" />
              Preview
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link href={`/campaigns/${id}/edit`}>
              <PencilIcon data-icon="inline-start" />
              Edit
            </Link>
          </Button>
          <div className="ml-auto">
            <CampaignActionsMenu
              campaignId={id}
              campaignName={name}
              status={campaign.status}
              eventCount={metrics.views + metrics.interactions}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
