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
 * touch minimum.
 */
export function LandingHeroActions() {
  return (
    <div className="mt-8 flex flex-wrap gap-3">
      <Show when="signed-in">
        <Button asChild size="lg" className="h-11 px-5 text-sm">
          <Link href={env.authRoutes.afterSignIn}>
            Go to campaigns
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        </Button>
        <Button asChild variant="outline" size="lg" className="h-11 px-5 text-sm">
          <Link href="/campaigns/new">Create a campaign</Link>
        </Button>
      </Show>

      <Show when="signed-out">
        <Button asChild size="lg" className="h-11 px-5 text-sm">
          <Link href={env.authRoutes.signUp}>
            Start a campaign
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        </Button>
        <Button asChild variant="outline" size="lg" className="h-11 px-5 text-sm">
          <Link href="#how-it-works">See how it works</Link>
        </Button>
      </Show>
    </div>
  );
}
