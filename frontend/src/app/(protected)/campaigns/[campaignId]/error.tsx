"use client";

import { RefreshCwIcon } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { PageShell } from "../../_components/page-shell";
import { Button } from "@/components/ui/button";

/**
 * The boundary for a single campaign's screens.
 *
 * A campaign that does not exist, or belongs to someone else, is already
 * handled as a 404 by `loadCampaign`, so anything reaching here is an outage
 * rather than a bad URL - and the way out is a retry, with the dashboard as
 * the fallback.
 */
export default function CampaignError({
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
    <PageShell className="flex flex-col items-start gap-4 py-20">
      <h1 className="font-heading text-2xl font-semibold tracking-tight">
        This campaign could not be loaded
      </h1>
      <p className="max-w-prose leading-relaxed text-pretty text-muted-foreground">
        The ClipPilot API did not answer. It is usually temporary - try again, and check that the
        backend is running if it keeps happening.
      </p>
      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">Reference: {error.digest}</p>
      ) : null}
      <div className="flex gap-2">
        <Button onClick={retry} size="lg">
          <RefreshCwIcon data-icon="inline-start" />
          Try again
        </Button>
        <Button asChild variant="outline" size="lg">
          <Link href="/dashboard">Back to campaigns</Link>
        </Button>
      </div>
    </PageShell>
  );
}
