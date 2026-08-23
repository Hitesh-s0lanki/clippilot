import { ArrowLeftIcon, PencilRulerIcon, SparklesIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { getAgentCatalogue } from "@/lib/api/agents";

import { PageHeader } from "../../_components/page-header";
import { PageShell } from "../../_components/page-shell";
import { StartOptionCard } from "./_components/start-option-card";

export const metadata: Metadata = {
  title: "New campaign",
  description: "Draft a campaign from a brief, or build one field by field.",
};

/**
 * How do you want to start?
 *
 * Two real routes rather than a toggle: each is a URL that can be shared and
 * returned to, and the back button moves between them.
 *
 * When the server has no model key the generated option stays on screen and
 * says why. Hiding it would be tidier and less honest - the capability exists,
 * it is the deployment that is missing a key.
 */
export default async function NewCampaignPage() {
  const catalogue = await getAgentCatalogue();

  return (
    <PageShell className="flex flex-col gap-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5 self-start">
        <Link href="/dashboard">
          <ArrowLeftIcon data-icon="inline-start" />
          All campaigns
        </Link>
      </Button>

      <PageHeader title="New campaign" description="How would you like to start?" />

      <ul className="grid gap-4 sm:grid-cols-2">
        <StartOptionCard
          Icon={SparklesIcon}
          badge="Personalised"
          title="Draft it for me"
          description="Describe the goal. The agent reads your site and your competitors, then writes the campaign and its ads."
          points={[
            "Researches what your competitors are already saying",
            "Writes the copy, the call to action and both response buttons",
            "You review everything before anything is saved",
          ]}
          href="/campaigns/generate"
          unavailable={
            catalogue.enabled
              ? undefined
              : "Unavailable on this server: no model key is configured."
          }
        />

        <StartOptionCard
          Icon={PencilRulerIcon}
          title="Build it myself"
          description="Fill in the campaign field by field, then add its ads."
          points={[
            "Full control over every setting",
            "Only a name is needed to save a draft",
            "Add up to five ads once the campaign exists",
          ]}
          href="/campaigns/new/manual"
        />
      </ul>
    </PageShell>
  );
}
