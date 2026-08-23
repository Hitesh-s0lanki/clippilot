import { PageShell } from "../_components/page-shell";
import { Skeleton } from "@/components/ui/skeleton";

import { CampaignListSkeleton } from "./_components/campaign-list-skeleton";
import { DashboardSummarySkeleton } from "./_components/dashboard-summary-skeleton";

/** The dashboard's shape while the listing loads, so nothing jumps into place. */
export default function DashboardLoading() {
  return (
    <PageShell className="space-y-8" aria-busy>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <Skeleton className="h-9 w-56" />
          <Skeleton className="h-4 w-96 max-w-full" />
        </div>
        <Skeleton className="h-9 w-40" />
      </div>

      <DashboardSummarySkeleton />

      <div className="space-y-4">
        <div className="flex items-baseline justify-between gap-3">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3 sm:flex-row">
          <Skeleton className="h-9 flex-1" />
          <Skeleton className="h-9 w-full sm:w-44" />
        </div>
        <CampaignListSkeleton />
      </div>
    </PageShell>
  );
}
