"use client";

import { LibraryIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

/**
 * The one destination in the header that anyone can reach.
 *
 * A Client Component only because the current route has to be marked, which
 * needs the path. `aria-current` carries that state for assistive technology
 * and the filled pill carries it visually, so it does not rest on colour
 * alone.
 *
 * Below `sm` the label is dropped and the icon stands alone in a 44px square.
 * Three labelled controls do not fit across a 360px bar - the words wrapped
 * onto a second line and broke the bar's height - and the brand is the one
 * worth keeping, so this is what gives way. `aria-label` keeps the name for
 * anyone not reading the icon.
 */
export function PrimaryNav() {
  const pathname = usePathname();
  const active = pathname === "/ads" || pathname.startsWith("/ads/");

  return (
    <nav aria-label="Browse" className="flex items-center">
      <Link
        href="/ads"
        aria-current={active ? "page" : undefined}
        aria-label="Ads library"
        className={cn(
          "inline-flex size-11 items-center justify-center gap-1.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none sm:h-9 sm:w-auto sm:px-3",
          active
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
        )}
      >
        <LibraryIcon aria-hidden className="size-4" />
        <span className="hidden sm:inline">Ads library</span>
      </Link>
    </nav>
  );
}
