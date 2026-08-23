"use client";

import { Button } from "@/components/ui/button";

import { PageShell } from "../_components/page-shell";

/**
 * The audience listing failed to load.
 *
 * Says what could not be reached and offers the retry, rather than leaving the
 * console on a blank shell with no way forward.
 */
export default function AudiencesError({ reset }: { error: Error; reset: () => void }) {
  return (
    <PageShell className="space-y-4">
      <h1 className="font-heading text-2xl font-semibold tracking-tight">
        Your audiences could not be loaded
      </h1>
      <p className="max-w-prose text-muted-foreground">
        The lists are still there - this screen just could not reach the API. Try again, and if it
        keeps failing check that the backend is running.
      </p>
      <Button onClick={reset}>Try again</Button>
    </PageShell>
  );
}
