"use client";

import { ArrowRightIcon, ChevronRightIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar,
} from "@/components/ui/sidebar";
import type { CampaignSummary } from "@/types/campaign";

import { CAMPAIGNS_LINK, NEW_CAMPAIGN_LINK, currentCampaignId } from "../_lib/nav-links";

export interface AppSidebarCampaignMenuProps {
  /** The newest few campaigns. Plain data - no icons cross the boundary. */
  campaigns: CampaignSummary[];
  /** Every campaign the owner has, which is what "view all" counts. */
  total: number;
}

const ACTIVE_ROW =
  "data-active:bg-card data-active:text-foreground data-active:shadow-xs data-active:ring-1 data-active:ring-border data-active:[&_svg]:text-primary";

/**
 * The campaigns branch of the rail: a few real campaigns, not just a link to
 * the list.
 *
 * Naming the last five turns navigation into recognition - the campaign you
 * were editing ten minutes ago is one click away instead of a trip through the
 * dashboard and a scan of a card grid. The rail deliberately stops at five and
 * hands off: a sidebar that grows with the account stops being navigation.
 *
 * Open by default because these are the product's primary destinations; the
 * disclosure is there to get them out of the way, not to hide them.
 */
export function AppSidebarCampaignMenu({ campaigns, total }: AppSidebarCampaignMenuProps) {
  const pathname = usePathname();
  const { state, isMobile } = useSidebar();
  const openCampaignId = currentCampaignId(pathname);
  const hidden = total - campaigns.length;

  // Collapsed to icons, the sub-list is hidden by the sidebar's own CSS, so a
  // disclosure here would be a control that visibly does nothing. The row
  // becomes a plain link to the full list instead, and takes over showing that
  // a campaign is open, since the child row that normally carries it is not on
  // screen. The mobile sheet always renders full width, so it is excluded.
  if (state === "collapsed" && !isMobile) {
    return (
      <SidebarMenuItem>
        <SidebarMenuButton
          asChild
          isActive={Boolean(openCampaignId)}
          tooltip={CAMPAIGNS_LINK.label}
          className={ACTIVE_ROW}
        >
          <Link href={CAMPAIGNS_LINK.href}>
            <CAMPAIGNS_LINK.Icon aria-hidden />
            <span>{CAMPAIGNS_LINK.label}</span>
          </Link>
        </SidebarMenuButton>
      </SidebarMenuItem>
    );
  }

  return (
    <Collapsible defaultOpen className="group/campaigns">
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton tooltip={CAMPAIGNS_LINK.label}>
            <CAMPAIGNS_LINK.Icon aria-hidden />
            <span>{CAMPAIGNS_LINK.label}</span>
            <ChevronRightIcon
              aria-hidden
              className="ml-auto text-muted-foreground transition-transform duration-200 group-data-open/campaigns:rotate-90"
            />
          </SidebarMenuButton>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <SidebarMenuSub>
            <SidebarMenuSubItem>
              <SidebarMenuSubButton asChild isActive={pathname === NEW_CAMPAIGN_LINK.href}>
                <Link
                  href={NEW_CAMPAIGN_LINK.href}
                  aria-current={pathname === NEW_CAMPAIGN_LINK.href ? "page" : undefined}
                >
                  <NEW_CAMPAIGN_LINK.Icon aria-hidden />
                  <span>{NEW_CAMPAIGN_LINK.label}</span>
                </Link>
              </SidebarMenuSubButton>
            </SidebarMenuSubItem>

            {campaigns.map((campaign) => {
              const active = campaign.id === openCampaignId;

              return (
                <SidebarMenuSubItem key={campaign.id}>
                  <SidebarMenuSubButton asChild isActive={active}>
                    {/* The builder, not the campaign root: it is the screen
                        someone returning to a campaign almost always wants. */}
                    <Link
                      href={`/campaigns/${campaign.id}/edit`}
                      aria-current={active ? "page" : undefined}
                      title={campaign.name}
                    >
                      <span>{campaign.name}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              );
            })}

            {hidden > 0 ? (
              <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild className="text-muted-foreground">
                  <Link href={CAMPAIGNS_LINK.href}>
                    <ArrowRightIcon aria-hidden />
                    <span>View all {total}</span>
                  </Link>
                </SidebarMenuSubButton>
              </SidebarMenuSubItem>
            ) : null}
          </SidebarMenuSub>
        </CollapsibleContent>
      </SidebarMenuItem>
    </Collapsible>
  );
}
