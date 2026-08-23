import { PublicChrome } from "@/components/layout/public-chrome";

/**
 * The chrome every page anyone can reach shares.
 *
 * In a layout rather than in each page, so `loading.tsx` and `error.tsx` -
 * which are siblings of a page, not children of it - get the header and footer
 * too. A page that rendered its own chrome flashed a bare skeleton on
 * navigation and dropped a failed request onto a screen with no way back.
 *
 * One layout for the whole group: the landing page and the ads library are the
 * same site wearing the same chrome, and `/ads` no longer needs a layout of its
 * own to say so.
 *
 * `PublicChrome` is a fragment, so header, page and footer stay direct flex
 * children of `<body>`. That is what keeps the footer's `mt-auto` working.
 */
export default function PublicLayout({ children }: LayoutProps<"/">) {
  return <PublicChrome>{children}</PublicChrome>;
}
