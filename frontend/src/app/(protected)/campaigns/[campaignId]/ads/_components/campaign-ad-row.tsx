import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { AD_EFFECTIVE_STATUS_LABELS } from "@/lib/campaign-labels";
import { CTA_LABELS, type CampaignAd } from "@/types/campaign";

import { AdStatusActions } from "./ad-status-actions";

export interface CampaignAdRowProps {
  campaignId: string;
  ad: CampaignAd;
}

const STATUS_VARIANT: Record<string, "default" | "secondary" | "warning" | "destructive"> = {
  ACTIVE: "default",
  DRAFT: "secondary",
  PAUSED: "warning",
  ARCHIVED: "secondary",
  INCOMPLETE: "destructive",
  CAMPAIGN_PAUSED: "warning",
};

/** One ad: what it says, what state it is in, and what can be done to it. */
export function CampaignAdRow({ campaignId, ad }: CampaignAdRowProps) {
  return (
    <li className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-heading font-semibold tracking-tight">
              <Link
                href={`/campaigns/${campaignId}/ads/${ad.id}`}
                className="underline-offset-4 hover:underline"
              >
                {ad.name}
              </Link>
            </h3>
            <Badge variant={STATUS_VARIANT[ad.effective_status] ?? "secondary"}>
              {AD_EFFECTIVE_STATUS_LABELS[ad.effective_status]}
            </Badge>
            <Badge variant="secondary">{CTA_LABELS[ad.cta]}</Badge>
          </div>

          {ad.headline ? (
            <p className="mt-1.5 truncate text-sm font-medium text-foreground">{ad.headline}</p>
          ) : null}
          {ad.personalised_message ? (
            <p className="mt-0.5 line-clamp-2 text-sm text-pretty text-muted-foreground">
              {ad.personalised_message}
            </p>
          ) : null}

          {ad.blockers.length > 0 ? (
            <p className="mt-2 text-xs text-destructive">
              Needs {ad.blockers.length === 1 ? "one more field" : `${ad.blockers.length} fields`}{" "}
              before it can run.
            </p>
          ) : null}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Link
            href={`/campaigns/${campaignId}/ads/${ad.id}`}
            className="text-sm font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          >
            Edit
          </Link>
          <Link
            href={`/campaigns/${campaignId}/preview?ad_id=${ad.id}`}
            className="text-sm font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          >
            Preview
          </Link>
          <AdStatusActions campaignId={campaignId} ad={ad} />
        </div>
      </div>
    </li>
  );
}
