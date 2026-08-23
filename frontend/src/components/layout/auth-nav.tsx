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
 * drift from what the proxy redirects to. The signed-in half is only the user
 * menu - the console links live in `MainNav`, which marks the active route.
 */
export function AuthNav() {
  return (
    <>
      <Show when="signed-out">
        <Button asChild variant="ghost" size="sm">
          <Link href={env.authRoutes.signIn}>Sign in</Link>
        </Button>
        <Button asChild size="sm">
          <Link href={env.authRoutes.signUp}>Get started</Link>
        </Button>
      </Show>

      <Show when="signed-in">
        <UserButton />
      </Show>
    </>
  );
}
