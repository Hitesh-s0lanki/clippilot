import { AppLogo } from "@/components/layout/app-logo";
import { siteConfig } from "@/config/site";

import { AuthBrandBackdrop } from "./auth-brand-backdrop";
import { AuthFlowList } from "./auth-flow-list";

/**
 * The left half of the account screens.
 *
 * It carries the product context the form column has no room for: the mark,
 * the promise, and the shape of the journey. It deliberately stops there - the
 * long description that used to sit under the headline said the same thing the
 * headline says, and a wall of copy beside a sign-in form competes with the one
 * thing the visitor came to do.
 *
 * The mark is pinned to the top and everything else is centred as one block, so
 * the panel does not split into two clumps with a hole between them the way
 * `justify-between` leaves it at full viewport height.
 *
 * An `<aside>` with an `<h2>`, not an `<h1>`: the page's main heading is the one
 * Clerk renders inside the card, and two competing `<h1>`s would leave a screen
 * reader without a single obvious title.
 */
export function AuthBrandPanel() {
  return (
    <aside className="relative hidden flex-col overflow-y-auto border-r border-border bg-card p-10 lg:flex xl:p-14">
      <AuthBrandBackdrop />

      <div className="relative flex items-center gap-3">
        <AppLogo size={36} className="rounded-xl" />
        <div>
          <p className="font-heading font-semibold tracking-tight">{siteConfig.name}</p>
          <p className="text-sm text-muted-foreground">Campaign console</p>
        </div>
      </div>

      {/* `my-auto` rather than `justify-center`: it centres the block without
          clipping the top of it when the panel is shorter than its content. */}
      <div className="relative my-auto max-w-xl space-y-10 py-10">
        <h2 className="font-heading text-3xl font-semibold tracking-tight text-balance xl:text-4xl">
          {siteConfig.headline}
        </h2>
        <AuthFlowList />
      </div>
    </aside>
  );
}
