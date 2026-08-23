import type { CampaignSummary } from "@/types/campaign";

import { CampaignCard } from "./campaign-card";

export interface CampaignListProps {
  campaigns: CampaignSummary[];
}

/**
 * The card grid.
 *
 * A list rather than a bare stack of divs: this is an enumeration of campaigns,
 * so a screen reader should announce how many there are before reading them.
 */
export function CampaignList({ campaigns }: CampaignListProps) {
  return (
    <ul className="grid gap-4 lg:grid-cols-2">
      {campaigns.map((campaign) => (
        <li key={campaign.id}>
          <CampaignCard campaign={campaign} />
        </li>
      ))}
    </ul>
  );
}
