import type { PublicCampaignCard } from "@/types/public";

import { AdsCard } from "./ads-card";

export interface AdsGridProps {
  ads: PublicCampaignCard[];
}

export function AdsGrid({ ads }: AdsGridProps) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {ads.map((ad) => (
        <AdsCard key={ad.ad_id} ad={ad} />
      ))}
    </ul>
  );
}
