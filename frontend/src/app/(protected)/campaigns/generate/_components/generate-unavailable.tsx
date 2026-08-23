import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * Agents are switched off on this deployment.
 *
 * Named rather than hidden: the feature exists, it needs a key, and saying so
 * is more useful than a screen that quietly does nothing.
 */
export function GenerateUnavailable() {
  return (
    <div className="rounded-xl border border-dashed border-border bg-card px-6 py-12 text-center">
      <h2 className="font-heading font-semibold tracking-tight">Generation is switched off</h2>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-pretty text-muted-foreground">
        This server has no model key configured, so the campaign strategist cannot run. Set
        <code className="mx-1 rounded bg-muted px-1 py-0.5 text-xs">ANTHROPIC_API_KEY</code>
        on the API to turn it on.
      </p>
      <Button asChild size="sm" className="mt-5">
        <Link href="/campaigns/new/manual">Build a campaign yourself</Link>
      </Button>
    </div>
  );
}
