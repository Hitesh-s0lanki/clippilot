import { SidebarMenuItem, SidebarMenuSkeleton } from "@/components/ui/sidebar";

import { SIDEBAR_CAMPAIGN_LIMIT } from "../_lib/sidebar-campaigns";

/**
 * The campaigns branch while the list streams in.
 *
 * One row for the branch itself plus the rows it is about to hold, so the
 * account row below does not slide down the rail when the names arrive.
 */
export function AppSidebarCampaignsSkeleton() {
  return (
    <>
      <SidebarMenuItem>
        <SidebarMenuSkeleton showIcon />
      </SidebarMenuItem>
      {Array.from({ length: SIDEBAR_CAMPAIGN_LIMIT }, (_, index) => (
        <SidebarMenuItem key={index} className="pl-3.5">
          <SidebarMenuSkeleton />
        </SidebarMenuItem>
      ))}
    </>
  );
}
