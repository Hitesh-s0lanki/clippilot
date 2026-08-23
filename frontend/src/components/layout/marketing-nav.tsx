"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { siteConfig } from "@/config/site";

/**
 * Section links in the site header, for a visitor who has not signed in.
 *
 * Every entry is an anchor into the landing page, so it renders only while the
 * landing page is the one on screen - a Client Component purely because that
 * needs the current path. Anywhere else the links would point at sections that
 * are not there, which is why this returns `null` rather than scrolling a
 * different route to a heading it does not have.
 *
 * Hidden below `md`: four labels do not fit beside the mark on a phone, and
 * the hero already carries a "See how it works" button that reaches the same
 * place.
 */
export function MarketingNav() {
  const pathname = usePathname();

  if (pathname !== "/") return null;

  return (
    <nav aria-label="Sections" className="ml-2 hidden items-center gap-1 md:flex">
      {siteConfig.sectionNav.map(({ label, href }) => (
        <Link
          key={href}
          href={href}
          className="inline-flex h-8 items-center rounded-lg px-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
