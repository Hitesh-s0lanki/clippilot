import { EyeIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { CampaignRecipient } from "@/types/campaign";

import { RecipientSwitcher } from "./recipient-switcher";

export interface OwnerPreviewToolbarProps {
  recipients: CampaignRecipient[];
  selectedId: string;
  /** Variables the resolver could not fill, surfaced before a recipient sees them. */
  unresolved: string[];
}

/**
 * The one piece of chrome the customer never sees.
 *
 * It says plainly that this is a dry run - nothing is recorded here, so the
 * numbers on the analytics tab stay honest - and it is where the recipient
 * switcher lives when a campaign has more than one.
 */
export function OwnerPreviewToolbar({
  recipients,
  selectedId,
  unresolved,
}: OwnerPreviewToolbarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-muted/60 px-3 py-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">
          <EyeIcon aria-hidden />
          Preview
        </Badge>
        <p className="text-sm text-muted-foreground">
          Clicks here are not recorded and do not appear in analytics.
        </p>
      </div>

      {unresolved.length > 0 ? (
        <p className="text-sm text-warning">
          Unknown {unresolved.length === 1 ? "variable" : "variables"}:{" "}
          {unresolved.map((name) => `{{${name}}}`).join(", ")}
        </p>
      ) : null}

      {recipients.length > 1 ? (
        <RecipientSwitcher recipients={recipients} selectedId={selectedId} />
      ) : null}
    </div>
  );
}
