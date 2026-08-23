import { Skeleton } from "@/components/ui/skeleton";

/** Holds the analytics layout while the aggregates are computed. */
export default function AnalyticsLoading() {
  return (
    <div aria-busy className="space-y-6">
      <div className="rounded-xl bg-primary/5 p-6 ring-1 ring-primary/20">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="mt-3 h-11 w-32" />
        <Skeleton className="mt-3 h-4 w-56" />
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((tile) => (
          <div key={tile} className="rounded-xl bg-card p-4 ring-1 ring-foreground/10">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="mt-2 h-8 w-16" />
          </div>
        ))}
      </div>

      <div className="space-y-4 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-full rounded-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    </div>
  );
}
