import { Skeleton } from "@/components/ui/skeleton";

import { PageShell } from "../_components/page-shell";

/**
 * The shape of the audience list, not a spinner.
 *
 * Three cards at the real height, so the header does not jump when the data
 * lands.
 */
export default function AudiencesLoading() {
  return (
    <PageShell className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-5 w-96 max-w-full" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((index) => (
          <Skeleton key={index} className="h-40 rounded-xl" />
        ))}
      </div>
    </PageShell>
  );
}
