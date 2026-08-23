import { ArrowLeftIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Button } from "@/components/ui/button";
import { listAds } from "@/lib/api/ads";
import { getUploadConfig } from "@/lib/api/uploads";
import { MAX_ADS_PER_CAMPAIGN } from "@/types/campaign";

import { AdForm } from "../../../_components/ad-form";
import { loadCampaign } from "../../../_lib/load-campaign";

export const metadata: Metadata = { title: "New ad" };

/**
 * Add one creative to a campaign.
 *
 * The ceiling is checked here as well as server-side: arriving at a form that
 * can only fail on submit is worse than not being offered it, and the Add
 * button on the list is hidden at the limit for the same reason.
 */
export default async function NewAdPage({ params }: PageProps<"/campaigns/[campaignId]/ads/new">) {
  const { campaignId } = await params;
  const [campaign, ads, uploads] = await Promise.all([
    loadCampaign(campaignId),
    listAds(campaignId),
    getUploadConfig(),
  ]);

  if (ads.total >= MAX_ADS_PER_CAMPAIGN) notFound();

  return (
    <div className="space-y-5">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5">
        <Link href={`/campaigns/${campaignId}/ads`}>
          <ArrowLeftIcon data-icon="inline-start" />
          All ads
        </Link>
      </Button>

      <div>
        <h1 className="font-heading text-lg font-semibold tracking-tight">Add an ad</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Ad {ads.total + 1} of {MAX_ADS_PER_CAMPAIGN} for {campaign.name}.
        </p>
      </div>

      <AdForm campaignId={campaignId} campaignName={campaign.name} uploads={uploads} />
    </div>
  );
}
