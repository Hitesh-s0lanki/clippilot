import { EyeIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { AudienceMember } from "@/types/audience";

import { MemberSwitcher } from "./member-switcher";

export interface OwnerPreviewToolbarProps {
  members: AudienceMember[];
  selectedId: string;
  /** Variables the resolver could not fill, surfaced before a customer sees them. */
  unresolved: string[];
}

/**
 * The one piece of chrome the customer never sees.
 *
 * It says plainly that this is a dry run - nothing is recorded here, so the
 * numbers on the analytics tab stay honest - and it is where the customer
 * switcher lives when a campaign has more than one.
 */
export function OwnerPreviewToolbar({ members, selectedId, unresolved }: OwnerPreviewToolbarProps) {
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

      {members.length > 1 ? <MemberSwitcher members={members} selectedId={selectedId} /> : null}
    </div>
  );
}
