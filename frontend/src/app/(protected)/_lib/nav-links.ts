import { HomeIcon, LayoutGridIcon, PlusIcon, type LucideIcon } from "lucide-react";

export interface NavLink {
  href: string;
  label: string;
  Icon: LucideIcon;
  /**
   * Routes that should light this link up even though the path is not an exact
   * match - a campaign's own screens belong to "Campaigns", not to nothing.
   */
  matches?: readonly string[];
}

export interface NavGroup {
  label: string;
  links: readonly NavLink[];
}

/**
 * The console's destinations, grouped as the rail shows them.
 *
 * One definition, read by the sidebar nav and by the topbar's section label, so
 * a renamed link cannot say "Campaigns" in one place and "Dashboard" in the
 * other. `matches` exists because `/campaigns/<id>/edit` has no nav entry of
 * its own but is unmistakably part of the campaigns section.
 *
 * `Icon` holds the component rather than a name string, which means this module
 * can only be read from a Client Component - a lucide icon is a `forwardRef`
 * object and React refuses to serialise it across the server boundary. That is
 * why `AppSidebar` passes a group *key* and the nav resolves the links itself,
 * rather than being handed an array of them.
 */
export const NAV_GROUPS = {
  console: {
    label: "Console",
    links: [
      {
        href: "/dashboard",
        label: "Campaigns",
        Icon: LayoutGridIcon,
        matches: ["/campaigns"],
      },
      {
        href: "/campaigns/new",
        label: "New campaign",
        Icon: PlusIcon,
      },
    ],
  },
  /** Reachable, but not where the work starts. */
  more: {
    label: "More",
    links: [
      {
        href: "/",
        label: "Product overview",
        Icon: HomeIcon,
      },
    ],
  },
} as const satisfies Record<string, NavGroup>;

export type NavGroupKey = keyof typeof NAV_GROUPS;

// The callback's return type is annotated because `as const` makes each group's
// `links` a readonly tuple, which `flatMap` will not widen on its own.
const ALL_LINKS: readonly NavLink[] = Object.values(NAV_GROUPS).flatMap(
  (group): readonly NavLink[] => group.links,
);

/**
 * Whether `pathname` is inside the section a link owns.
 *
 * Exact match first, then the declared prefixes. `/campaigns/new` has its own
 * entry, so it is excluded from the `/campaigns` prefix - otherwise both links
 * would claim the same URL and two items would read as current.
 */
export function isNavLinkActive(link: NavLink, pathname: string): boolean {
  if (pathname === link.href) return true;

  return (link.matches ?? []).some(
    (prefix) =>
      pathname.startsWith(`${prefix}/`) &&
      !ALL_LINKS.some((other) => other.href !== link.href && other.href === pathname),
  );
}

/** The label for whichever section `pathname` sits in, for the topbar. */
export function activeNavLabel(pathname: string): string | undefined {
  return ALL_LINKS.find((link) => isNavLinkActive(link, pathname))?.label;
}
