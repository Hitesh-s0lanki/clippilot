import Link from "next/link";

import { AppLogo } from "@/components/layout/app-logo";
import { AuthNav } from "@/components/layout/auth-nav";
import { PrimaryNav } from "@/components/layout/primary-nav";
import { siteConfig } from "@/config/site";

/**
 * The app shell's floating top bar.
 *
 * An island rather than a full-width band: the sticky wrapper is transparent
 * and the bar inside it is a bordered, blurred card, so the page's own colour
 * runs behind and past it. The landing page pulls its hero up under this with
 * a matching negative margin, which is what lets the gradient reach the top of
 * the window instead of starting below a header strip.
 *
 * The bar carries four things and stops there - the mark, the ads library,
 * the dashboard and the account menu. Campaign navigation belongs to the
 * console itself, not to a bar that a signed-out visitor also sees, and the
 * theme follows the operating system rather than costing a fifth control.
 */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 px-3 pt-3">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center gap-2 rounded-2xl border border-border bg-background/75 px-3 shadow-lg shadow-foreground/5 backdrop-blur-xl sm:px-4">
        <Link
          href="/"
          className="flex min-h-11 items-center gap-2 rounded-lg focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none sm:min-h-0"
        >
          <AppLogo size={28} />
          <span className="font-heading font-semibold tracking-tight">{siteConfig.name}</span>
        </Link>

        <div className="ml-auto flex items-center gap-1.5">
          <PrimaryNav />
          <AuthNav />
        </div>
      </div>
    </header>
  );
}
