import { Show } from "@clerk/nextjs";
import Link from "next/link";

import { AppLogo } from "@/components/layout/app-logo";
import { AuthNav } from "@/components/layout/auth-nav";
import { MainNav } from "@/components/layout/main-nav";
import { MarketingNav } from "@/components/layout/marketing-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { siteConfig } from "@/config/site";

/**
 * The app shell's top bar.
 *
 * The console links are inside `<Show when="signed-in">` so the landing page,
 * which renders the same chrome, does not offer routes a visitor cannot reach.
 * A signed-out visitor gets the landing page's section anchors instead -
 * `MarketingNav` hides itself everywhere those sections do not exist.
 */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center gap-3 px-5">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-lg focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <AppLogo size={28} />
          <span className="font-heading font-semibold tracking-tight">{siteConfig.name}</span>
        </Link>

        <Show when="signed-in">
          <span aria-hidden className="hidden h-5 w-px bg-border sm:block" />
          <MainNav />
        </Show>

        <Show when="signed-out">
          <MarketingNav />
        </Show>

        <nav aria-label="Account" className="ml-auto flex items-center gap-1.5">
          <ThemeToggle />
          <AuthNav />
        </nav>
      </div>
    </header>
  );
}
