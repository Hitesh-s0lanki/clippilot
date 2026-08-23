"use client";

import { ArrowLeftIcon, RotateCcwIcon } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { AppLogo } from "@/components/layout/app-logo";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/config/site";

import { ErrorChecklist } from "./_components/error-checklist";

/**
 * Route-level boundary for uncaught exceptions. Expected failures - a campaign
 * that is not live, a validation rejection - are handled where they happen; only
 * genuine bugs and outages should land here.
 *
 * It brings its own minimal header rather than `PublicChrome`: an error
 * boundary is a Client Component, and the site header resolves the session on
 * the server. A logo that links home is all this screen needs anyway.
 */
export default function RouteError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  /** Re-fetches and re-renders the segment. Preferred over `reset`, which only clears state. */
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-start justify-center px-5 py-16 sm:py-24">
      <Link
        href="/"
        className="flex items-center gap-2 rounded-lg focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
      >
        <AppLogo size={28} />
        <span className="font-heading font-semibold tracking-tight">{siteConfig.name}</span>
      </Link>

      <p className="mt-12 font-mono text-sm font-medium text-destructive">Error</p>
      <h1 className="mt-3 max-w-2xl font-heading text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
        This screen could not be rendered.
      </h1>
      <p className="mt-4 max-w-xl leading-relaxed text-pretty text-muted-foreground">
        Nothing you had saved is affected - the failure happened while drawing the page, not while
        writing to it. It is usually temporary, so trying again is the first thing worth doing.
      </p>

      {error.digest ? (
        <p className="mt-4 rounded-lg border border-border bg-muted/50 px-3 py-1.5 font-mono text-xs text-muted-foreground">
          Reference: {error.digest}
        </p>
      ) : null}

      <div className="mt-8 flex flex-wrap gap-3">
        <Button onClick={retry} size="lg" className="h-11 px-5 text-sm">
          <RotateCcwIcon data-icon="inline-start" />
          Try again
        </Button>
        <Button asChild variant="outline" size="lg" className="h-11 px-5 text-sm">
          <Link href="/">
            <ArrowLeftIcon data-icon="inline-start" />
            Back to the home page
          </Link>
        </Button>
      </div>

      <ErrorChecklist />
    </main>
  );
}
