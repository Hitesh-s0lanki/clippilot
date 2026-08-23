import { PlusIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { MAX_ADS_PER_CAMPAIGN } from "@/types/campaign";

export interface AdsEmptyStateProps {
  campaignId: string;
}

/**
 * No creatives yet.
 *
 * This is where a new campaign lands, so it is the instruction rather than an
 * apology: the campaign is saved, and the next thing to do is add the video.
 */
export function AdsEmptyState({ campaignId }: AdsEmptyStateProps) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card px-6 py-12 text-center">
      <h3 className="font-heading font-semibold tracking-tight">Add your first ad</h3>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-pretty text-muted-foreground">
        An ad is the video a customer watches, with its headline, its message and its two response
        buttons. A campaign needs at least one finished ad before it can be published, and can hold
        up to {MAX_ADS_PER_CAMPAIGN} to test different angles.
      </p>
      <Button asChild size="sm" className="mt-5">
        <Link href={`/campaigns/${campaignId}/ads/new`}>
          <PlusIcon data-icon="inline-start" />
          Add an ad
        </Link>
      </Button>
    </div>
  );
}
