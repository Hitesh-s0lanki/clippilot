import { UsersIcon } from "lucide-react";

import { AudienceCreateDialog } from "./audience-create-dialog";

export interface AudienceEmptyStateProps {
  /** A search that matched nothing is a different message from having none. */
  searching?: boolean;
}

/** Nothing to list yet, and the one action that changes that. */
export function AudienceEmptyState({ searching = false }: AudienceEmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-14 text-center">
      <UsersIcon aria-hidden className="size-8 text-muted-foreground" />
      <h2 className="font-heading text-lg font-semibold tracking-tight">
        {searching ? "No audience matched" : "No audiences yet"}
      </h2>
      <p className="max-w-md text-sm text-pretty text-muted-foreground">
        {searching
          ? "Try a shorter search, or create a new list."
          : "An audience is the list a campaign is sent to. Upload a CSV of the people you have, or add them one at a time - only a name is required."}
      </p>
      {searching ? null : <AudienceCreateDialog />}
    </div>
  );
}
