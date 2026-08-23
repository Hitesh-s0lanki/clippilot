import type { ReactNode } from "react";

import { SiteHeader } from "@/components/layout/site-header";

import { PublicFooter } from "./public-footer";

export interface PublicChromeProps {
  children: ReactNode;
}

/**
 * Header and marketing footer around the pages anyone can reach.
 *
 * The mirror of `SiteChrome`, which the console uses: same header, different
 * footer. A fragment rather than a wrapper, because `PublicFooter` is pinned
 * with `mt-auto` and that only works while it is a direct flex child of
 * `<body>`.
 */
export function PublicChrome({ children }: PublicChromeProps) {
  return (
    <>
      <SiteHeader />
      {children}
      <PublicFooter />
    </>
  );
}
