import { SendIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { CampaignEffectiveStatus } from "@/types/campaign";

export interface AnalyticsEmptyStateProps {
  campaignId: string;
  status: CampaignEffectiveStatus;
}

/**
 * No events yet - which has two very different causes.
 *
 * A live campaign nobody has opened needs its link shared; a draft has not
 * been published at all. Telling a draft owner to "wait for responses" would
 * send them off to wait for something that cannot happen.
 */
export function AnalyticsEmptyState({ campaignId, status }: AnalyticsEmptyStateProps) {
  const live = status === "ACTIVE";

  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-12 text-center">
      <span
        aria-hidden
        className="flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground"
      >
        <SendIcon className="size-5" />
      </span>
      <h2 className="font-heading text-base font-medium">
        {live ? "Nothing recorded yet" : "This campaign is not live yet"}
      </h2>
      <p className="max-w-md text-pretty text-muted-foreground">
        {live
          ? "Views and responses appear here the moment a recipient opens their link. Copy it from the header above to send it out."
          : "Analytics start filling in once the campaign is published and a recipient opens it. Try it yourself from the preview tab first."}
      </p>
      <Button asChild variant="outline" size="lg" className="mt-1">
        <Link href={`/campaigns/${campaignId}/${live ? "preview" : "edit"}`}>
          {live ? "Open the preview" : "Back to the builder"}
        </Link>
      </Button>
    </div>
  );
}
