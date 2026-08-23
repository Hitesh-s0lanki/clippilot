import Link from "next/link";

import { siteConfig } from "@/config/site";

/**
 * The console's footer - one line, and nothing that competes with the screen
 * above it. The public pages get `PublicFooter` instead, which carries the
 * site map; a signed-in user reading their dashboard has no use for it.
 */
export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-2 px-5 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p>{siteConfig.name} · interactive video campaigns</p>
        <nav aria-label="Footer" className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-sm transition-colors hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            Campaigns
          </Link>
          <Link
            href="/campaigns/new"
            className="rounded-sm transition-colors hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            New campaign
          </Link>
        </nav>
      </div>
    </footer>
  );
}
