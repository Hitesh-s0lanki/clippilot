import { PreviewFrame } from "@/components/campaign/preview-frame";
import { Skeleton } from "@/components/ui/skeleton";

/** The preview's shape while it loads, so the video box never jumps into place. */
export default function PreviewLoading() {
  return (
    <PreviewFrame>
      <div aria-busy className="space-y-6">
        <Skeleton className="aspect-video w-full rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="mx-auto h-6 w-2/3" />
          <Skeleton className="mx-auto h-4 w-full" />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Skeleton className="h-12 rounded-lg" />
          <Skeleton className="h-12 rounded-lg" />
        </div>
      </div>
    </PreviewFrame>
  );
}
