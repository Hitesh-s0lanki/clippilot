import type { Metadata } from "next";

import { PreviewFrame } from "@/components/campaign/preview-frame";
import { PreviewStage } from "@/components/campaign/preview-stage";
import { isApiError } from "@/lib/api/errors";
import { getPublicPreview } from "@/lib/api/public";
import type { CampaignPreview } from "@/types/preview";

import {
  PreviewUnavailable,
  type PreviewUnavailableReason,
} from "./_components/preview-unavailable";

export const metadata: Metadata = {
  title: "Your video",
  description: "A personalised video, and two ways to reply.",
  // Recipient links are private by nature; they have no business in an index.
  robots: { index: false, follow: false },
};

type Outcome =
  { ok: true; preview: CampaignPreview } | { ok: false; reason: PreviewUnavailableReason };

/**
 * Resolves the failures a recipient can legitimately hit, and only those.
 *
 * `403` is a paused or unpublished campaign, `422` one with no video yet, and
 * `404` a link that no longer resolves. All three are states this screen
 * renders in the recipient's own language; anything else is a real outage and
 * belongs to the error boundary.
 */
async function loadPreview(campaignId: string, recipientId?: string): Promise<Outcome> {
  try {
    return { ok: true, preview: await getPublicPreview(campaignId, recipientId) };
  } catch (error) {
    if (!isApiError(error)) throw error;
    if (error.status === 403) return { ok: false, reason: "not-live" };
    if (error.status === 422) return { ok: false, reason: "incomplete" };
    if (error.status === 404) return { ok: false, reason: "unknown-link" };
    throw error;
  }
}

export default async function PublicPreviewPage({
  params,
  searchParams,
}: PageProps<"/preview/[campaignId]">) {
  const { campaignId } = await params;
  const { recipient_id: recipientId } = await searchParams;

  const outcome = await loadPreview(
    campaignId,
    typeof recipientId === "string" ? recipientId : undefined,
  );

  if (!outcome.ok) {
    return (
      <PreviewFrame>
        <PreviewUnavailable reason={outcome.reason} />
      </PreviewFrame>
    );
  }

  return (
    <PreviewFrame eyebrow={`For ${outcome.preview.customer_name}`}>
      <PreviewStage preview={outcome.preview} />
    </PreviewFrame>
  );
}
