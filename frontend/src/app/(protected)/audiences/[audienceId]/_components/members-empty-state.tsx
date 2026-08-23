import { UsersIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

import { MemberAddDialog } from "./member-add-dialog";
import { MemberImportDialog } from "./member-import-dialog";

export interface MembersEmptyStateProps {
  audienceId: string;
  /** An empty list and a filter that matched nothing need different words. */
  filtered: boolean;
}

/** Nothing to show, and the action that fixes whichever reason it is. */
export function MembersEmptyState({ audienceId, filtered }: MembersEmptyStateProps) {
  if (filtered) {
    return (
      <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center">
        <p className="font-medium">Nobody matches that</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-pretty text-muted-foreground">
          The people are still in the list - this combination of filters just has no one in it.
        </p>
        <Button variant="outline" size="sm" className="mt-4" asChild>
          <Link href={`/audiences/${audienceId}`}>Clear filters</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-12 text-center">
      <UsersIcon aria-hidden className="size-8 text-muted-foreground" />
      <p className="font-medium">This audience is empty</p>
      <p className="max-w-md text-sm text-pretty text-muted-foreground">
        Upload a CSV of the people you have, or add one by hand. Only a name is required - age,
        city, country, email and phone are all optional, and whatever you do provide becomes a
        segment you can target.
      </p>
      <div className="flex gap-2">
        <MemberImportDialog audienceId={audienceId} />
        <MemberAddDialog audienceId={audienceId} />
      </div>
    </div>
  );
}
