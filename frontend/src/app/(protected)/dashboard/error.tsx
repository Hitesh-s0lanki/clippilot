"use client";

import { RefreshCwIcon, TriangleAlertIcon } from "lucide-react";
import { useEffect } from "react";

import { PageShell } from "../_components/page-shell";
import { Button } from "@/components/ui/button";
import { env } from "@/lib/env";

/**
 * The dashboard's own boundary.
 *
 * The single most likely failure here is that the API is not running, so the
 * message says that and where it was expected, rather than the generic
 * "something went wrong" the root boundary shows.
 */
export default function DashboardError({
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
      <span
        aria-hidden
        className="flex size-11 items-center justify-center rounded-xl bg-destructive/10 text-destructive"
      >
        <TriangleAlertIcon className="size-5" />
      </span>
      <h1 className="font-heading text-2xl font-semibold tracking-tight">
        Campaigns could not be loaded
      </h1>
      <p className="max-w-prose leading-relaxed text-pretty text-muted-foreground">
        The console could not reach the ClipPilot API at{" "}
        <span className="font-mono text-sm">{env.apiBaseUrl}</span>. Start the backend with{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
          uv run uvicorn src.main:app --reload
        </code>{" "}
        and try again.
      </p>
      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">Reference: {error.digest}</p>
      ) : null}
      <Button onClick={retry} size="lg">
        <RefreshCwIcon data-icon="inline-start" />
        Try again
      </Button>
    </PageShell>
  );
}
