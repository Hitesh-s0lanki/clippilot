import { AppLogo } from "@/components/layout/app-logo";
import { siteConfig } from "@/config/site";

import { AuthBrandBackdrop } from "./auth-brand-backdrop";
import { AuthFlowList } from "./auth-flow-list";

/**
 * The wide half of the account screens - three of the split's four columns.
 *
 * It carries the product context that the form column has no room for: the
 * mark, the promise, and the four steps a campaign moves through. An `<aside>`
 * with an `<h2>`, not an `<h1>`: the page's main heading is the one Clerk
 * renders inside the card, and two competing `<h1>`s would leave a screen
 * reader without a single obvious title.
 *
 * Hidden below `xl`. At narrower widths a quarter-viewport form column is too
 * cramped for a sign-in card, so the split collapses and this panel steps
 * aside rather than shrinking into an unreadable strip.
 */
export function AuthBrandPanel() {
  return (
    <aside className="relative hidden flex-col justify-between gap-16 overflow-hidden border-r border-border bg-card p-14 xl:flex 2xl:p-20">
      <AuthBrandBackdrop />

      <div className="relative flex items-center gap-3">
        <AppLogo size={36} className="rounded-xl" />
        <div>
          <p className="font-heading font-semibold tracking-tight">{siteConfig.name}</p>
          <p className="text-sm text-muted-foreground">Campaign console</p>
        </div>
      </div>

      <div className="relative max-w-2xl">
        <h2 className="font-heading text-4xl font-semibold tracking-tight text-balance 2xl:text-5xl">
          {siteConfig.headline}
        </h2>
        <p className="mt-5 text-base leading-relaxed text-pretty text-muted-foreground">
          {siteConfig.description}
        </p>
      </div>

      <div className="relative">
        <AuthFlowList />
      </div>
    </aside>
  );
}
