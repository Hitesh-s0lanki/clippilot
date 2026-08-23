import { VideoOffIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export interface PreviewNotReadyProps {
  campaignId: string;
}

/**
 * What the owner sees before a video has been configured.
 *
 * The preview endpoint cannot render a campaign with no video, and this is the
 * screen that says so with the fix attached rather than an error code.
 */
export function PreviewNotReady({ campaignId }: PreviewNotReadyProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-14 text-center">
      <span
        aria-hidden
        className="flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground"
      >
        <VideoOffIcon className="size-5" />
      </span>
      <h2 className="font-heading text-base font-medium">Nothing to preview yet</h2>
      <p className="max-w-sm text-pretty text-muted-foreground">
        A campaign needs a video before it can be rendered. Add one in the builder and this view
        will show exactly what the recipient sees.
      </p>
      <Button asChild size="lg" className="mt-1">
        <Link href={`/campaigns/${campaignId}/edit`}>Add a video</Link>
      </Button>
    </div>
  );
}
