import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export interface CampaignListSkeletonProps {
  /** Match what the page is about to render so the grid does not resize. */
  count?: number;
}

/** The card grid's shape while the listing loads. */
export function CampaignListSkeleton({ count = 4 }: CampaignListSkeletonProps) {
  return (
    <div aria-hidden className="grid gap-4 lg:grid-cols-2">
      {Array.from({ length: count }, (_, index) => (
        <Card key={index}>
          <CardContent className="flex flex-col gap-3">
            <div className="flex items-start gap-3">
              <Skeleton className="aspect-video w-20 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <Skeleton className="h-5 w-20 rounded-4xl" />
            </div>
            <Skeleton className="h-3 w-1/2" />
            <div className="border-t border-border pt-3">
              <Skeleton className="h-8 w-24" />
            </div>
            <div className="flex gap-2 border-t border-border pt-3">
              <Skeleton className="h-7 w-24" />
              <Skeleton className="h-7 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
