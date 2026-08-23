import { Show, UserButton } from "@clerk/nextjs";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { env } from "@/lib/env";

/**
 * Session controls in the site header.
 *
 * A Server Component: `<Show>` resolves the session on the server, so the
 * header never flashes signed-out markup before Clerk hydrates. Core 3
 * replaced `<SignedIn>` / `<SignedOut>` with the single `<Show when>`.
 *
 * Links point at the app's own `/login` and `/register` rather than Clerk's
 * hosted pages, and read those paths from `env.authRoutes` so they cannot
 * drift from what the proxy redirects to.
 *
 * One button per session state, and only one. Signed out that is "Get
 * started": a second "Sign in" beside it splits a single decision into two
 * and, since the sign-up card already offers to switch, buys nothing. Signed
 * in it is "Dashboard" - which signed out would only land on the sign-in page
 * anyway. Someone who already has an account still reaches `/login` from the
 * sign-up screen, from the footer, or by being redirected there by the proxy.
 *
 * Both are the same slot seen by the two halves of the audience, so they share
 * a shape: the header's one primary action, drawn as a pill. `rounded-4xl`
 * rather than `rounded-full` keeps it on the `--radius` scale, and at this
 * height it resolves to a pill anyway.
 */
export function AuthNav() {
  return (
    <>
      <Show when="signed-out">
        <Button asChild size="sm" className="h-11 rounded-4xl px-4 sm:h-9">
          <Link href={env.authRoutes.signUp}>Get started</Link>
        </Button>
      </Show>

      <Show when="signed-in">
        <Button asChild size="sm" className="h-11 rounded-4xl px-4 sm:h-9">
          <Link href={env.authRoutes.afterSignIn}>Dashboard</Link>
        </Button>
        <UserButton />
      </Show>
    </>
  );
}
