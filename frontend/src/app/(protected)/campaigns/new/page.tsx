import { ArrowLeftIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { listAudiences } from "@/lib/api/audiences";

import { PageHeader } from "../../_components/page-header";
import { PageShell } from "../../_components/page-shell";
import { CampaignBuilder } from "../_components/campaign-builder";

export const metadata: Metadata = {
  title: "New campaign",
  description: "Configure a personalised video campaign field by field.",
};

/**
 * The campaign form.
 *
 * Settings only - the creatives are added on the campaign's own ads screen
 * once it exists, which is where saving lands.
 */
export default async function NewCampaignPage() {
  const audiences = await listAudiences();

  return (
    <PageShell className="flex flex-col gap-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5 self-start">
        <Link href="/dashboard">
          <ArrowLeftIcon data-icon="inline-start" />
          All campaigns
        </Link>
      </Button>

      <PageHeader title="Build a campaign" />

      <CampaignBuilder audiences={audiences.items} />
    </PageShell>
  );
}
