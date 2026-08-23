"use client";

import { RefreshCwIcon } from "lucide-react";
import { useEffect } from "react";

import { PreviewFrame } from "@/components/campaign/preview-frame";
import { Button } from "@/components/ui/button";

/**
 * The recipient's error boundary.
 *
 * Kept in the recipient's language: no stack, no API origin, no mention of a
 * campaign console they have never heard of. Just the one thing they can
 * usefully do.
 */
export default function PreviewError({ error, retry }: { error: Error; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <PreviewFrame>
      <div className="flex flex-col items-center gap-3 rounded-xl bg-card px-6 py-14 text-center ring-1 ring-foreground/10">
        <h1 className="font-heading text-lg font-medium">This video could not be loaded</h1>
        <p className="max-w-sm leading-relaxed text-pretty text-muted-foreground">
          Something went wrong on the way here. It is usually temporary.
        </p>
        <Button onClick={retry} size="lg" className="min-h-11 px-5">
          <RefreshCwIcon data-icon="inline-start" />
          Try again
        </Button>
      </div>
    </PreviewFrame>
  );
}
