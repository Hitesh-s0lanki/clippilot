import Link from "next/link";

import { AppLogo } from "@/components/layout/app-logo";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { siteConfig } from "@/config/site";

/**
 * The product mark at the top of the sidebar.
 *
 * Rendered as a menu button rather than a bare link so it keeps the same
 * height, padding and hover target as the nav items below it - the header
 * should read as the first row of the rail, not as a separate widget bolted on
 * top. `size="lg"` is what shadcn's sidebar reserves for the brand and account
 * rows; it is also what keeps the mark square once the rail collapses to icons.
 */
export function AppSidebarBrand() {
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton asChild size="lg" className="gap-2.5">
          <Link href="/dashboard">
            <AppLogo size={32} className="size-8 shrink-0 rounded-md" />
            <span className="grid min-w-0 flex-1 leading-tight">
              <span className="truncate font-heading text-sm font-semibold tracking-tight">
                {siteConfig.name}
              </span>
              <span className="truncate text-xs text-muted-foreground">Campaign console</span>
            </span>
          </Link>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
