import {
  LayoutDashboardIcon,
  PlayCircleIcon,
  PlusIcon,
  UsersIcon,
  type LucideIcon,
} from "lucide-react";

export interface NavLink {
  href: string;
  label: string;
  Icon: LucideIcon;
}

/**
 * The console's fixed destinations.
 *
 * Only the entries whose URL is known without loading anything live here - the
 * campaign rows in the rail come from the API and are built in
 * `AppSidebarCampaignMenu` instead.
 *
 * `Icon` holds the component rather than a name string, so this module can only
 * be read from a Client Component: a lucide icon is a `forwardRef` object and
 * React refuses to serialise it across the server boundary.
 */
export const OVERVIEW_LINK: NavLink = {
  href: "/dashboard",
  label: "Dashboard",
  Icon: LayoutDashboardIcon,
};

export const CAMPAIGNS_LINK: NavLink = {
  href: "/dashboard",
  label: "Campaigns",
  Icon: PlayCircleIcon,
};

export const NEW_CAMPAIGN_LINK: NavLink = {
  href: "/campaigns/new",
  label: "New campaign",
  Icon: PlusIcon,
};

export const AUDIENCES_LINK: NavLink = {
  href: "/audiences",
  label: "Audiences",
  Icon: UsersIcon,
};

/** `/campaigns/<id>/…` - a campaign's own screens, which have no fixed URL. */
const CAMPAIGN_DETAIL = /^\/campaigns\/(?!new(?:\/|$))([^/]+)/;

/** The id of the campaign the current path belongs to, if it is inside one. */
export function currentCampaignId(pathname: string): string | undefined {
  return CAMPAIGN_DETAIL.exec(pathname)?.[1];
}

/**
 * The name of the section a path sits in, for the topbar.
 *
 * Derived rather than stored per route: a campaign's builder, preview and
 * analytics screens are all "Campaigns", and none of them has a nav entry of
 * its own to hang a label on.
 */
export function activeSectionLabel(pathname: string): string | undefined {
  if (pathname === OVERVIEW_LINK.href) return OVERVIEW_LINK.label;
  if (pathname === NEW_CAMPAIGN_LINK.href) return NEW_CAMPAIGN_LINK.label;
  if (pathname.startsWith(AUDIENCES_LINK.href)) return AUDIENCES_LINK.label;
  if (currentCampaignId(pathname)) return CAMPAIGNS_LINK.label;

  return undefined;
}
