import { PlusIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { MAX_ADS_PER_CAMPAIGN } from "@/types/campaign";

export interface AdsToolbarProps {
  campaignId: string;
  total: number;
}

/** The count against the ceiling, and the way to add another. */
export function AdsToolbar({ campaignId, total }: AdsToolbarProps) {
  const full = total >= MAX_ADS_PER_CAMPAIGN;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 className="font-heading text-lg font-semibold tracking-tight">Ads</h2>
        <p className="text-sm text-muted-foreground">
          {total} of {MAX_ADS_PER_CAMPAIGN} creatives. Each one has its own status.
        </p>
      </div>

      {full ? (
        // Disabled rather than hidden: the ceiling is worth seeing, and a
        // button that vanishes reads as a bug.
        <Button size="sm" disabled title={`A campaign holds at most ${MAX_ADS_PER_CAMPAIGN} ads.`}>
          <PlusIcon data-icon="inline-start" />
          Add ad
        </Button>
      ) : (
        <Button asChild size="sm">
          <Link href={`/campaigns/${campaignId}/ads/new`}>
            <PlusIcon data-icon="inline-start" />
            Add ad
          </Link>
        </Button>
      )}
    </div>
  );
}
