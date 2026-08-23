import { Skeleton } from "@/components/ui/skeleton";

import { AdsGridSkeleton } from "./_components/ads-grid-skeleton";

export default function AdsLoading() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 space-y-8 px-5 py-12 sm:py-16">
      <div className="space-y-3">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-9 w-full max-w-lg" />
        <Skeleton className="h-4 w-full max-w-2xl" />
      </div>
      <AdsGridSkeleton />
    </main>
  );
}
