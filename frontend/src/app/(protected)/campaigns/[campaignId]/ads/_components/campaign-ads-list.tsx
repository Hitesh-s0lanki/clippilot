import type { AdEffectiveStatus, CampaignAd } from "@/types/campaign";

import { CampaignAdRow } from "./campaign-ad-row";

export interface CampaignAdsListProps {
  campaignId: string;
  ads: CampaignAd[];
  campaignStatus: string;
}

/** Every ad on the campaign, in creation order. */
export function CampaignAdsList({ campaignId, ads, campaignStatus }: CampaignAdsListProps) {
  const anyBlockedByCampaign = ads.some(
    (ad) => (ad.effective_status as AdEffectiveStatus) === "CAMPAIGN_PAUSED",
  );

  return (
    <div className="space-y-3">
      {anyBlockedByCampaign ? (
        <p className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
          One or more ads are switched on but not delivering: this campaign is{" "}
          <span className="font-medium text-foreground">{campaignStatus.toLowerCase()}</span>.
          Publish or resume the campaign to put them live.
        </p>
      ) : null}

      <ul className="space-y-3">
        {ads.map((ad) => (
          <CampaignAdRow key={ad.id} campaignId={campaignId} ad={ad} />
        ))}
      </ul>
    </div>
  );
}
