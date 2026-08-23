import { PageShell } from "../../_components/page-shell";
import { loadCampaign } from "../_lib/load-campaign";
import { CampaignHeader } from "./_components/campaign-header";
import { CampaignTabs } from "./_components/campaign-tabs";

/**
 * The shell shared by a campaign's three views.
 *
 * The campaign is fetched here for the header and again by each page for its
 * own content - `getCampaign` is wrapped in React's `cache`, so both resolve
 * from one request rather than two.
 */
export default async function CampaignLayout({
  children,
  params,
}: LayoutProps<"/campaigns/[campaignId]">) {
  const { campaignId } = await params;
  const campaign = await loadCampaign(campaignId);

  return (
    <PageShell className="space-y-6">
      <CampaignHeader campaign={campaign} />
      <CampaignTabs campaignId={campaign.id} />
      {children}
    </PageShell>
  );
}
