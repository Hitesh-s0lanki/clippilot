import type { ReactNode } from "react";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";

export interface SiteChromeProps {
  children: ReactNode;
}

/**
 * Header and footer around a screen that wants the app shell.
 *
 * The chrome used to sit in the root layout, which meant every route got it -
 * including the account screens, whose two-sided layout runs edge to edge and
 * has no room for a second header. Rendering it here instead lets each route
 * group opt in: `(protected)` and the landing page do, `(auth)` does not.
 *
 * A fragment rather than a wrapper: `<SiteFooter>` is pinned with `mt-auto`,
 * which only works while it is a direct flex child of `<body>`.
 */
export function SiteChrome({ children }: SiteChromeProps) {
  return (
    <>
      <SiteHeader />
      {children}
      <SiteFooter />
    </>
  );
}
