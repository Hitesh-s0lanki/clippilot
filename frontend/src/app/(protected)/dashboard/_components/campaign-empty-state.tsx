import { PlusIcon, SearchXIcon, VideoIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export interface CampaignEmptyStateProps {
  /** `true` when filters are hiding results rather than there being none. */
  filtered: boolean;
}

/**
 * The two empty states, which are not the same problem.
 *
 * "You have no campaigns" wants the create action; "no campaign matches this
 * filter" wants the filter cleared. Showing one message for both sends half of
 * the people who see it in the wrong direction.
 */
export function CampaignEmptyState({ filtered }: CampaignEmptyStateProps) {
  if (filtered) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-14 text-center">
        <SearchXIcon aria-hidden className="size-6 text-muted-foreground" />
        <h2 className="font-heading text-base font-medium">No campaigns match these filters</h2>
        <p className="max-w-sm text-pretty text-muted-foreground">
          Try a different status, or clear the search to see everything again.
        </p>
        <Button asChild variant="outline" size="lg" className="mt-1">
          <Link href="/dashboard">Clear filters</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-16 text-center">
      <span
        aria-hidden
        className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary"
      >
        <VideoIcon className="size-5" />
      </span>
      <h2 className="font-heading text-lg font-medium">Create your first campaign</h2>
      <p className="max-w-md text-pretty text-muted-foreground">
        A campaign is one personalised video, a message that greets the customer by name, and two
        response options. Build one, preview it as the customer sees it, and read the responses back
        here.
      </p>
      <Button asChild size="lg" className="mt-1">
        <Link href="/campaigns/new">
          <PlusIcon data-icon="inline-start" />
          Create campaign
        </Link>
      </Button>
    </div>
  );
}
