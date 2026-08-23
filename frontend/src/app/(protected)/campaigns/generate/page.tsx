import { ArrowLeftIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Button } from "@/components/ui/button";
import { getAgentCatalogue } from "@/lib/api/agents";
import { listAudiences } from "@/lib/api/audiences";

import { PageHeader } from "../../_components/page-header";
import { PageShell } from "../../_components/page-shell";
import { GenerateCampaign } from "./_components/generate-campaign";
import { GenerateUnavailable } from "./_components/generate-unavailable";

export const metadata: Metadata = {
  title: "Generate a campaign",
  description: "Research a business and its competitors, then draft the campaign.",
};

/**
 * Draft a campaign from a brief.
 *
 * The catalogue is read first: agents are off on a deployment with no model
 * key, and a screen that can only fail is worse than one that says why.
 */
export default async function GenerateCampaignPage() {
  const [catalogue, audiences] = await Promise.all([getAgentCatalogue(), listAudiences()]);

  const strategist = catalogue.agents.find((agent) => agent.name === "campaign-strategist");
  if (!strategist) notFound();

  return (
    <PageShell className="flex flex-col gap-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5 self-start">
        <Link href="/campaigns/new/manual">
          <ArrowLeftIcon data-icon="inline-start" />
          Build it myself
        </Link>
      </Button>

      <PageHeader
        eyebrow="Generate"
        title="Draft a campaign from a brief"
        description="Say what you want the campaign to do. The agent works out the rest — who you are, who you compete with, and what nobody is saying — then drafts the campaign and its ads for you to review."
      />

      {catalogue.enabled ? (
        <GenerateCampaign audiences={audiences.items} />
      ) : (
        <GenerateUnavailable />
      )}
    </PageShell>
  );
}
