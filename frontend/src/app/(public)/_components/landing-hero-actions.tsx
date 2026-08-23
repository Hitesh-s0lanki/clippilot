import { Show } from "@clerk/nextjs";
import { ArrowRightIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { env } from "@/lib/env";

/**
 * The page's primary call to action, in both hero and closing band.
 *
 * What it offers depends on whether there is a session, resolved on the server
 * by `<Show>`: someone already signed in wants their campaigns, not a "Get
 * started" button that lands them where they already are.
 *
 * The buttons are raised to 44px rather than the default control height -
 * these are the two targets the whole page exists to hit, and 44px is the
 * touch minimum. On a phone they go full width and stack: side by side they
 * wrapped anyway, and two buttons of different widths on their own rows read
 * as an accident rather than a pair.
 */
export function LandingHeroActions() {
  return (
    <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
      <Show when="signed-in">
        <Button asChild size="lg" className="h-11 w-full px-5 text-sm sm:w-auto">
          <Link href={env.authRoutes.afterSignIn}>
            Go to campaigns
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        </Button>
        <Button asChild variant="outline" size="lg" className="h-11 w-full px-5 text-sm sm:w-auto">
          <Link href="/campaigns/new">Create a campaign</Link>
        </Button>
      </Show>

      <Show when="signed-out">
        <Button asChild size="lg" className="h-11 w-full px-5 text-sm sm:w-auto">
          <Link href={env.authRoutes.signUp}>
            Start a campaign
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        </Button>
        <Button asChild variant="outline" size="lg" className="h-11 w-full px-5 text-sm sm:w-auto">
          <Link href="#how-it-works">See how it works</Link>
        </Button>
      </Show>
    </div>
  );
}
