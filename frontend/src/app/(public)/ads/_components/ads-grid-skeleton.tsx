import { Skeleton } from "@/components/ui/skeleton";

/** Matches the loaded grid's shape, so the page does not jump when data lands. */
export function AdsGridSkeleton() {
  return (
    <ul aria-hidden className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[0, 1, 2, 3, 4, 5].map((card) => (
        <li key={card} className="overflow-hidden rounded-2xl border border-border bg-card">
          <Skeleton className="aspect-video rounded-none" />
          <div className="space-y-3 p-5">
            <Skeleton className="h-5 w-24 rounded-4xl" />
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </li>
      ))}
    </ul>
  );
}
