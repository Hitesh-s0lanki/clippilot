import { Skeleton } from "@/components/ui/skeleton";

/** Holds the strip's height while the portfolio totals stream in. */
export function DashboardSummarySkeleton() {
  return (
    <div aria-hidden className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {[0, 1, 2, 3].map((tile) => (
        <div key={tile} className="rounded-xl bg-card p-4 ring-1 ring-foreground/10">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="mt-2 h-8 w-16" />
        </div>
      ))}
    </div>
  );
}
