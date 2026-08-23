import { Suspense } from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar";

import { AppSidebarBrand } from "./app-sidebar-brand";
import { AppSidebarCampaigns } from "./app-sidebar-campaigns";
import { AppSidebarCampaignsSkeleton } from "./app-sidebar-campaigns-skeleton";
import { AppSidebarAudienceLink } from "./app-sidebar-audience-link";
import { AppSidebarOverviewLink } from "./app-sidebar-overview-link";
import { AppSidebarUser } from "./app-sidebar-user";

/**
 * The console's navigation rail.
 *
 * Grouped by what the row is about. "Console" is the work: the portfolio
 * overview, then the campaigns by name. "Audience" is who the work is aimed
 * at - a separate band because a list outlives any one campaign and is reached
 * on its own terms, not through one.
 *
 * `collapsible="icon"` rather than `offcanvas`: on a wide screen the rail
 * should be able to shrink to icons and give the content room back, without
 * disappearing entirely and leaving no visible way to navigate. Below the
 * mobile breakpoint shadcn swaps it for a sheet regardless.
 *
 * The campaign branch is the only data-backed one, and it streams inside its
 * own `Suspense` boundary so a slow list never delays the brand, the fixed
 * links or the account row. A Server Component - only the pieces that need the
 * current path or the session are clients.
 */
export function AppSidebar() {
  return (
    <Sidebar
      collapsible="icon"
      // The base layer paints every border with `--border`. The rail divides two
      // surfaces of its own, so it takes the sidebar's border token instead.
      className="border-sidebar-border"
    >
      <SidebarHeader>
        <AppSidebarBrand />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Console</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <AppSidebarOverviewLink />
              <Suspense fallback={<AppSidebarCampaignsSkeleton />}>
                <AppSidebarCampaigns />
              </Suspense>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Audience</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <AppSidebarAudienceLink />
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarSeparator className="mx-0" />

      <SidebarFooter>
        <AppSidebarUser />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
