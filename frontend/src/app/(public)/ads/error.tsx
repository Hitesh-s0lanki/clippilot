"use client";

import { RotateCcwIcon } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

/**
 * The library is a single read, so the only way to land here is that the API
 * did not answer. That is worth saying plainly rather than blaming the page.
 */
export default function AdsError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-start justify-center px-5 py-20">
      <p className="font-mono text-sm font-medium text-destructive">Error</p>
      <h1 className="mt-3 font-heading text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
        The ads library could not be loaded.
      </h1>
      <p className="mt-4 max-w-xl leading-relaxed text-pretty text-muted-foreground">
        The ClipPilot API did not answer. Nothing is wrong with the campaigns themselves - try again
        in a moment.
      </p>
      {error.digest ? (
        <p className="mt-4 rounded-lg border border-border bg-muted/50 px-3 py-1.5 font-mono text-xs text-muted-foreground">
          Reference: {error.digest}
        </p>
      ) : null}
      <Button onClick={retry} size="lg" className="mt-8 h-11 px-5 text-sm">
        <RotateCcwIcon data-icon="inline-start" />
        Try again
      </Button>
    </main>
  );
}
