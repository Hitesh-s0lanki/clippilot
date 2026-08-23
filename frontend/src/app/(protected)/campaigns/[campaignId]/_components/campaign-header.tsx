import { ArrowLeftIcon, ShieldCheckIcon } from "lucide-react";
import Link from "next/link";

import { CampaignActionsMenu } from "../../../_components/campaign-actions-menu";
import { CampaignStatusBadge } from "../../../_components/campaign-status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  OBJECTIVE_LABELS,
  SPECIAL_CATEGORY_CHIPS,
  formatRecipientCount,
} from "@/lib/campaign-labels";
import { isLive } from "@/lib/campaign-status";
import { formatDate } from "@/lib/format";
import type { Campaign } from "@/types/campaign";

import { CopyPreviewLink } from "./copy-preview-link";

export interface CampaignHeaderProps {
  campaign: Campaign;
}

/**
 * The identity bar above the builder, preview and analytics.
 *
 * Everything here answers "which campaign am I looking at, and is it running":
 * the derived status, the objective, the audience size and, once it is live,
 * the link a recipient would open. The compliance chip is an outline badge and
 * not an alarm colour - a declared special category is a disclosure, not a
 * warning.
 */
export function CampaignHeader({ campaign }: CampaignHeaderProps) {
  const category = campaign.compliance.special_category;
  const events = campaign.metrics.views + campaign.metrics.interactions;

  return (
    <div className="space-y-4">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5">
        <Link href="/dashboard">
          <ArrowLeftIcon data-icon="inline-start" />
          All campaigns
        </Link>
      </Button>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-heading text-2xl font-semibold tracking-tight text-balance">
              {campaign.name}
            </h1>
            <CampaignStatusBadge status={campaign.effective_status} />
            {category !== "NONE" ? (
              <Badge variant="outline">
                <ShieldCheckIcon aria-hidden />
                {SPECIAL_CATEGORY_CHIPS[category]}
              </Badge>
            ) : null}
          </div>

          <p className="text-sm text-muted-foreground">
            {OBJECTIVE_LABELS[campaign.objective]} ·{" "}
            {formatRecipientCount(campaign.audience.recipient_count)} · Created{" "}
            {formatDate(campaign.created_at, campaign.schedule.timezone)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {isLive(campaign.effective_status) ? (
            <CopyPreviewLink
              campaignId={campaign.id}
              recipientId={campaign.audience.recipients[0]?.id}
            />
          ) : null}
          <CampaignActionsMenu
            campaignId={campaign.id}
            campaignName={campaign.name}
            status={campaign.status}
            eventCount={events}
            redirectAfterDelete="/dashboard"
          />
        </div>
      </div>
    </div>
  );
}
