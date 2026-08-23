"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";

import { PageShell } from "../../_components/page-shell";

/** This audience could not be loaded. Offers the retry and the way back. */
export default function AudienceDetailError({ reset }: { error: Error; reset: () => void }) {
  return (
    <PageShell className="space-y-4">
      <h1 className="font-heading text-2xl font-semibold tracking-tight">
        This audience could not be loaded
      </h1>
      <p className="max-w-prose text-muted-foreground">
        The list and everyone on it are unaffected - this screen just could not reach the API.
      </p>
      <div className="flex gap-2">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" asChild>
          <Link href="/audiences">All audiences</Link>
        </Button>
      </div>
    </PageShell>
  );
}
