import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar";

import { AppSidebarBrand } from "./app-sidebar-brand";
import { AppSidebarNav } from "./app-sidebar-nav";
import { AppSidebarUser } from "./app-sidebar-user";

/**
 * The console's navigation rail.
 *
 * Three bands, top to bottom: what the product is, where you can go, and who
 * you are. That order is the whole point of moving navigation out of the top
 * bar - a horizontal strip has to compress those three jobs into one line and
 * ends up doing none of them well, while a rail gives each its own region and
 * still leaves the full page width for the screen itself.
 *
 * `collapsible="icon"` rather than `offcanvas`: on a wide screen the rail
 * should be able to shrink to icons and give the content room back, without
 * disappearing entirely and leaving no visible way to navigate. Below the
 * mobile breakpoint shadcn swaps it for a sheet regardless.
 *
 * A Server Component - only the two pieces that need the current path or the
 * session are clients.
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
        <AppSidebarNav group="console" />
        {/* Pushed to the bottom: the way out of the console, not a peer of the
            destinations inside it. */}
        <AppSidebarNav group="more" className="mt-auto" />
      </SidebarContent>

      <SidebarSeparator className="mx-0" />

      <SidebarFooter>
        <AppSidebarUser />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
