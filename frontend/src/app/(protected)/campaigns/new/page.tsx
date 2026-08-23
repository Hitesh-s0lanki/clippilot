import { ArrowLeftIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "../../_components/page-header";
import { PageShell } from "../../_components/page-shell";
import { Button } from "@/components/ui/button";
import { getUploadConfig } from "@/lib/api/uploads";

import { CampaignBuilder } from "../_components/campaign-builder";

export const metadata: Metadata = {
  title: "New campaign",
  description: "Configure a personalised video campaign and publish it to its recipients.",
};

export default async function NewCampaignPage() {
  const uploads = await getUploadConfig();

  return (
    <PageShell className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5">
        <Link href="/dashboard">
          <ArrowLeftIcon data-icon="inline-start" />
          All campaigns
        </Link>
      </Button>

      <PageHeader
        eyebrow="New campaign"
        title="Build a campaign"
        description="Only the name is needed to save a draft. Publishing runs the full contract and tells you everything that is still missing."
      />

      <CampaignBuilder uploads={uploads} />
    </PageShell>
  );
}
