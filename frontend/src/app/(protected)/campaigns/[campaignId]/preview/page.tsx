import type { Metadata } from "next";

import { PreviewStage } from "@/components/campaign/preview-stage";
import { getOwnerPreview } from "@/lib/api/campaigns";
import { isApiError } from "@/lib/api/errors";
import type { CampaignPreview } from "@/types/preview";

import { loadCampaign } from "../../_lib/load-campaign";
import { OwnerPreviewToolbar } from "./_components/owner-preview-toolbar";
import { PreviewNotReady } from "./_components/preview-not-ready";
import { resolveFollowUps } from "./_lib/resolve-follow-ups";

export const metadata: Metadata = { title: "Preview" };

/** `422` means the campaign has no video yet, which is a state, not a failure. */
async function loadPreview(
  campaignId: string,
  recipientId?: string,
): Promise<CampaignPreview | null> {
  try {
    return await getOwnerPreview(campaignId, recipientId);
  } catch (error) {
    if (isApiError(error) && error.status === 422) return null;
    throw error;
  }
}

export default async function CampaignPreviewPage({
  params,
  searchParams,
}: PageProps<"/campaigns/[campaignId]/preview">) {
  const { campaignId } = await params;
  const { recipient_id: requested } = await searchParams;

  const campaign = await loadCampaign(campaignId);
  const preview = await loadPreview(
    campaignId,
    typeof requested === "string" ? requested : undefined,
  );

  if (!preview) return <PreviewNotReady campaignId={campaignId} />;

  const recipients = campaign.audience.recipients;

  return (
    <div className="space-y-5">
      <OwnerPreviewToolbar
        recipients={recipients}
        selectedId={preview.recipient_id ?? recipients[0]?.id ?? ""}
        unresolved={preview.unresolved_variables}
      />

      <div className="mx-auto w-full max-w-2xl rounded-xl bg-card p-5 ring-1 ring-foreground/10 sm:p-6">
        <p className="mb-4 text-center text-sm text-muted-foreground">
          For {preview.customer_name}
        </p>
        <PreviewStage
          preview={preview}
          mode="owner"
          followUps={resolveFollowUps(campaign, preview.customer_name)}
        />
      </div>
    </div>
  );
}
