"use client";

import { UsersIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";

import { AUDIENCES_LINK } from "../_lib/nav-links";

/**
 * The audience side of the product: who receives a campaign.
 *
 * A plain link with a fixed URL, unlike the row it replaced. An audience used
 * to belong to one campaign, so the rail had to guess which campaign's list to
 * open and fall back to the newest one when the answer was "none" - which
 * meant the same row led somewhere different depending on where you clicked it
 * from. Audiences are account-level now, so there is one destination and it is
 * always this one.
 */
export function AppSidebarAudienceLink() {
  const pathname = usePathname();
  const active = pathname === AUDIENCES_LINK.href || pathname.startsWith("/audiences/");

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        asChild
        isActive={active}
        tooltip={AUDIENCES_LINK.label}
        className="data-active:bg-card data-active:text-foreground data-active:shadow-xs data-active:ring-1 data-active:ring-border data-active:[&_svg]:text-primary"
      >
        <Link href={AUDIENCES_LINK.href} aria-current={active ? "page" : undefined}>
          <UsersIcon aria-hidden />
          <span>{AUDIENCES_LINK.label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}
