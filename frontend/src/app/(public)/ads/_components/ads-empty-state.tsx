import { ArrowRightIcon, VideoOffIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { env } from "@/lib/env";

/**
 * Nothing is live.
 *
 * A genuinely common state rather than an edge case - the library only shows
 * campaigns whose owner has published them and whose schedule window is open
 * right now - so it explains the rule instead of just saying "no results".
 */
export function AdsEmptyState() {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-dashed border-border bg-card/40 px-6 py-16 text-center">
      <span className="grid size-11 place-items-center rounded-xl bg-muted">
        <VideoOffIcon aria-hidden className="size-5 text-muted-foreground" />
      </span>
      <h3 className="mt-4 font-heading font-semibold tracking-tight">Nothing is live right now</h3>
      <p className="mt-2 max-w-md leading-relaxed text-pretty text-muted-foreground">
        The library lists campaigns that are published and inside their schedule window. Drafts,
        paused campaigns and ones that have finished their run stay out of it.
      </p>
      <Button asChild className="mt-6 h-11 px-5 text-sm">
        <Link href={env.authRoutes.signUp}>
          Publish the first one
          <ArrowRightIcon data-icon="inline-end" />
        </Link>
      </Button>
    </div>
  );
}
