"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

import { NAV_GROUPS, isNavLinkActive, type NavGroupKey } from "../_lib/nav-links";

export interface AppSidebarNavProps {
  /**
   * A key, not the links themselves. Each link carries a lucide icon, which is
   * a `forwardRef` object rather than a plain value, so an array of them cannot
   * cross the boundary from the Server Component that renders this. Passing the
   * key and reading `NAV_GROUPS` here keeps the definition in one file and the
   * prop serialisable.
   */
  group: NavGroupKey;
  className?: string;
}

/**
 * One labelled group of destinations in the rail.
 *
 * A Client Component because the current path decides which row is current.
 * That state is carried three ways on purpose: `aria-current` for assistive
 * technology, a raised card surface for everyone, and a primary-hued icon - so
 * the current page never rests on colour alone (WCAG 1.4.1).
 *
 * `tooltip` is what the collapsed icon rail falls back on; shadcn only shows it
 * while `state === "collapsed"`, so it costs nothing when expanded.
 */
export function AppSidebarNav({ group, className }: AppSidebarNavProps) {
  const pathname = usePathname();
  const { label, links } = NAV_GROUPS[group];

  return (
    <SidebarGroup className={cn(className)}>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {links.map((link) => {
            const active = isNavLinkActive(link, pathname);

            return (
              <SidebarMenuItem key={link.href}>
                <SidebarMenuButton
                  asChild
                  isActive={active}
                  tooltip={link.label}
                  className="data-active:bg-card data-active:text-foreground data-active:shadow-xs data-active:ring-1 data-active:ring-border data-active:[&_svg]:text-primary"
                >
                  <Link href={link.href} aria-current={active ? "page" : undefined}>
                    <link.Icon aria-hidden />
                    <span>{link.label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
