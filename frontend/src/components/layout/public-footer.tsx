import { siteConfig } from "@/config/site";

import { PublicFooterBrand } from "./public-footer-brand";
import { PublicFooterNav } from "./public-footer-nav";

/**
 * The footer for the public shell - landing page and the top-level 404.
 *
 * Deliberately not the footer the console gets: a signed-in user reading their
 * dashboard has no use for three columns of marketing links, so
 * `SiteFooter` stays a single line and this one carries the site map.
 *
 * Every href here resolves. The console links sit behind the session guard, so
 * a signed-out visitor following one lands on sign-in rather than a dead end.
 *
 * Two columns from the smallest screen up, with the brand block spanning
 * both: three link lists stacked one per row turned the footer into its own
 * screenful of scrolling on a phone.
 *
 * `mt-auto` pins it to the bottom of short pages, which works only while it is
 * a direct flex child of `<body>` - see `PublicChrome`.
 */
export function PublicFooter() {
  return (
    <footer className="mt-auto border-t border-border bg-card/40">
      <div className="mx-auto w-full max-w-5xl px-5 py-12">
        <div className="grid grid-cols-2 gap-x-6 gap-y-10 lg:grid-cols-[minmax(0,1.6fr)_repeat(3,minmax(0,1fr))]">
          <PublicFooterBrand />
          {siteConfig.footerNav.map((column) => (
            <PublicFooterNav key={column.title} column={column} />
          ))}
        </div>

        <div className="mt-10 flex flex-col gap-2 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {new Date().getFullYear()} {siteConfig.name} · Interactive video campaigns
          </p>
          <p>A demonstration product. Not a live financial service.</p>
        </div>
      </div>
    </footer>
  );
}
