import { ArrowLeftIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Button } from "@/components/ui/button";
import { getAd } from "@/lib/api/ads";
import { isApiError } from "@/lib/api/errors";
import { getUploadConfig } from "@/lib/api/uploads";

import { AdForm } from "../../../_components/ad-form";
import { loadCampaign } from "../../../_lib/load-campaign";

export async function generateMetadata({
  params,
}: PageProps<"/campaigns/[campaignId]/ads/[adId]">): Promise<Metadata> {
  const { campaignId, adId } = await params;
  try {
    const ad = await getAd(campaignId, adId);
    return { title: `Edit ${ad.name}` };
  } catch {
    return { title: "Ad" };
  }
}

/** Edit one creative. */
export default async function EditAdPage({
  params,
}: PageProps<"/campaigns/[campaignId]/ads/[adId]">) {
  const { campaignId, adId } = await params;

  const [campaign, uploads] = await Promise.all([loadCampaign(campaignId), getUploadConfig()]);

  let ad;
  try {
    ad = await getAd(campaignId, adId);
  } catch (error) {
    // A 404 here is a real not-found, not a failure worth an error boundary.
    if (isApiError(error) && error.status === 404) notFound();
    throw error;
  }

  return (
    <div className="space-y-5">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5">
        <Link href={`/campaigns/${campaignId}/ads`}>
          <ArrowLeftIcon data-icon="inline-start" />
          All ads
        </Link>
      </Button>

      <div>
        <h1 className="font-heading text-lg font-semibold tracking-tight">{ad.name}</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">Creative for {campaign.name}.</p>
      </div>

      <AdForm campaignId={campaignId} campaignName={campaign.name} ad={ad} uploads={uploads} />
    </div>
  );
}
