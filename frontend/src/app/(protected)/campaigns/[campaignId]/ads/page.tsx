import type { Metadata } from "next";

import { listAds } from "@/lib/api/ads";

import { loadCampaign } from "../../_lib/load-campaign";
import { AdsEmptyState } from "./_components/ads-empty-state";
import { AdsToolbar } from "./_components/ads-toolbar";
import { CampaignAdsList } from "./_components/campaign-ads-list";

export const metadata: Metadata = { title: "Ads" };

/**
 * Every creative under one campaign.
 *
 * The builder edits the first ad inline; this is where the rest live, because
 * each one carries its own status and only a list makes that visible.
 */
export default async function CampaignAdsPage({
  params,
}: PageProps<"/campaigns/[campaignId]/ads">) {
  const { campaignId } = await params;
  const [campaign, ads] = await Promise.all([loadCampaign(campaignId), listAds(campaignId)]);

  return (
    <div className="space-y-5">
      <AdsToolbar campaignId={campaignId} total={ads.total} />

      {ads.total === 0 ? (
        <AdsEmptyState campaignId={campaignId} />
      ) : (
        <CampaignAdsList
          campaignId={campaignId}
          ads={ads.items}
          campaignStatus={campaign.effective_status}
        />
      )}
    </div>
  );
}
