"use client";

import { LayoutGridIcon, PlusIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/dashboard", label: "Campaigns", Icon: LayoutGridIcon },
  { href: "/campaigns/new", label: "New campaign", Icon: PlusIcon },
] as const;

/**
 * Console navigation in the site header.
 *
 * A Client Component only because the active item has to be marked, which
 * needs the current path. `aria-current` carries that state for assistive
 * technology; the underline carries it visually, so it does not rest on colour
 * alone.
 */
export function MainNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Console" className="flex items-center gap-1">
      {LINKS.map(({ href, label, Icon }) => {
        const active = pathname === href || (href === "/dashboard" && pathname === "/campaigns");

        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "inline-flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-sm font-medium transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
              active
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
            )}
          >
            <Icon aria-hidden className="size-3.5" />
            <span className="hidden sm:inline">{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
