import { Skeleton } from "@/components/ui/skeleton";
import { SidebarMenu, SidebarMenuItem } from "@/components/ui/sidebar";

/**
 * The footer row while Clerk resolves the session in the browser.
 *
 * Shaped like the row it stands in for - a 32px avatar square and two lines of
 * text at the height of a `size="lg"` menu button - so the rail does not change
 * height the moment the user loads.
 *
 * Hand-built rather than `SidebarMenuSkeleton`, which draws a single text line
 * and so would collapse to one bar where the real row has a name and an email.
 */
export function AppSidebarUserSkeleton() {
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <div className="flex h-12 items-center gap-2.5 rounded-md p-2">
          <Skeleton className="size-8 shrink-0 rounded-lg" />
          <div className="grid flex-1 gap-1.5 group-data-[collapsible=icon]:hidden">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-32" />
          </div>
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
