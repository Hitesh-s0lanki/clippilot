import { ArchiveIcon } from "lucide-react";
import type { Metadata } from "next";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { listAudiences } from "@/lib/api/audiences";

import { CampaignBuilder } from "../../_components/campaign-builder";
import { PublishChecklist } from "../../_components/publish-checklist";
import { loadCampaign } from "../../_lib/load-campaign";

export async function generateMetadata({
  params,
}: PageProps<"/campaigns/[campaignId]/edit">): Promise<Metadata> {
  const { campaignId } = await params;
  const campaign = await loadCampaign(campaignId);
  return { title: `Edit ${campaign.name}` };
}

export default async function CampaignEditPage({
  params,
}: PageProps<"/campaigns/[campaignId]/edit">) {
  const { campaignId } = await params;
  const campaign = await loadCampaign(campaignId);

  if (campaign.status === "ARCHIVED") {
    return (
      <Alert>
        <ArchiveIcon />
        <AlertTitle>This campaign is archived</AlertTitle>
        <AlertDescription>
          Archived campaigns are read-only, so their recorded analytics keep meaning what they
          meant. Its numbers are still on the analytics tab.
        </AlertDescription>
      </Alert>
    );
  }

  const audiences = await listAudiences();

  return (
    <div className="space-y-6">
      <PublishChecklist
        campaignId={campaign.id}
        blockers={campaign.publish_blockers}
        status={campaign.effective_status}
      />
      <CampaignBuilder campaign={campaign} audiences={audiences.items} />
    </div>
  );
}
