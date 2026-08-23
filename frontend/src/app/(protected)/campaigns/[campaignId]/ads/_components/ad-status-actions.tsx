"use client";

import { useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { changeAdStatusAction } from "@/lib/actions/ad-actions";
import type { AdStatus, CampaignAd } from "@/types/campaign";

export interface AdStatusActionsProps {
  campaignId: string;
  ad: CampaignAd;
}

/**
 * Switch one ad on or pause it.
 *
 * Switching on can be refused: the API enforces that ad's own completeness
 * contract and returns the fields it is missing, so the toast names them
 * rather than saying "not ready".
 */
export function AdStatusActions({ campaignId, ad }: AdStatusActionsProps) {
  const [pending, startTransition] = useTransition();
  const target: AdStatus = ad.status === "ACTIVE" ? "PAUSED" : "ACTIVE";

  if (ad.status === "ARCHIVED") {
    return <span className="text-sm text-muted-foreground">Archived</span>;
  }

  function move() {
    startTransition(async () => {
      const result = await changeAdStatusAction(campaignId, ad.id, target);

      if (!result.ok) {
        const fields = Object.keys(result.fieldErrors);
        toast.error(
          fields.length > 0 ? `${result.message} Missing: ${fields.join(", ")}.` : result.message,
        );
        return;
      }

      toast.success(target === "ACTIVE" ? "Ad switched on." : "Ad paused.");
    });
  }

  return (
    <Button
      size="sm"
      variant={target === "ACTIVE" ? "default" : "outline"}
      disabled={pending}
      onClick={move}
    >
      {target === "ACTIVE" ? "Switch on" : "Pause"}
    </Button>
  );
}
