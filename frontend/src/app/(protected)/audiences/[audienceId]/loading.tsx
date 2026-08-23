import { Skeleton } from "@/components/ui/skeleton";

import { PageShell } from "../../_components/page-shell";

/** The detail screen's shape: header, four tiles, breakdown, table. */
export default function AudienceDetailLoading() {
  return (
    <PageShell className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-72 max-w-full" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-24 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-48 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-72 rounded-xl" />
    </PageShell>
  );
}
