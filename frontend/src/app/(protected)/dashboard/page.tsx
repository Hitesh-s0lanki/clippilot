import { PlusIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { PageHeader } from "../_components/page-header";
import { PageShell } from "../_components/page-shell";
import { Button } from "@/components/ui/button";
import { listCampaigns } from "@/lib/api/campaigns";

import { CampaignEmptyState } from "./_components/campaign-empty-state";
import { CampaignFilters } from "./_components/campaign-filters";
import { CampaignList } from "./_components/campaign-list";
import { CampaignListHeading } from "./_components/campaign-list-heading";
import { CampaignPagination } from "./_components/campaign-pagination";
import { DashboardSummary } from "./_components/dashboard-summary";
import { DashboardSummarySkeleton } from "./_components/dashboard-summary-skeleton";
import { PAGE_SIZE, parseDashboardQuery } from "./_lib/dashboard-query";

export const metadata: Metadata = {
  title: "Campaigns",
  description: "Every campaign with its status, audience, views and interactions.",
};

export default async function DashboardPage({ searchParams }: PageProps<"/dashboard">) {
  const query = parseDashboardQuery(await searchParams);
  const page = await listCampaigns({
    status: query.status,
    search: query.search,
    includeArchived: query.includeArchived,
    limit: PAGE_SIZE,
    offset: query.offset,
  });

  return (
    <PageShell className="space-y-8">
      <PageHeader
        title="Campaigns"
        description="Build a personalised video journey, preview it as the customer sees it, and read the responses back here."
        actions={
          <Button asChild size="lg">
            <Link href="/campaigns/new">
              <PlusIcon data-icon="inline-start" />
              Create campaign
            </Link>
          </Button>
        }
      />

      <Suspense fallback={<DashboardSummarySkeleton />}>
        <DashboardSummary />
      </Suspense>

      <section aria-labelledby="campaign-list-heading" className="space-y-4">
        <CampaignListHeading total={page.total} filtered={query.filtered} />
        <CampaignFilters query={query} />
        {page.items.length === 0 ? (
          <CampaignEmptyState filtered={query.filtered} />
        ) : (
          <CampaignList campaigns={page.items} />
        )}
        <CampaignPagination query={query} total={page.total} shown={page.items.length} />
      </section>
    </PageShell>
  );
}
