"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";

import { OVERVIEW_LINK } from "../_lib/nav-links";

/**
 * The portfolio overview, above the campaigns branch.
 *
 * Its own row rather than a child of "Campaigns": the dashboard answers "how is
 * everything doing", which is a different question from "take me to a
 * campaign", and burying it in a disclosure would hide the one screen that
 * summarises the account.
 *
 * A Client Component because the current path decides whether it is current.
 * That state is carried three ways - `aria-current`, a raised card surface, and
 * a primary-hued icon - so it never rests on colour alone (WCAG 1.4.1).
 */
export function AppSidebarOverviewLink() {
  const active = usePathname() === OVERVIEW_LINK.href;

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        asChild
        isActive={active}
        tooltip={OVERVIEW_LINK.label}
        className="data-active:bg-card data-active:text-foreground data-active:shadow-xs data-active:ring-1 data-active:ring-border data-active:[&_svg]:text-primary"
      >
        <Link href={OVERVIEW_LINK.href} aria-current={active ? "page" : undefined}>
          <OVERVIEW_LINK.Icon aria-hidden />
          <span>{OVERVIEW_LINK.label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}
