import { ArrowLeftIcon } from "lucide-react";
import Link from "next/link";

import { formatCount } from "@/lib/format";
import type { Audience } from "@/types/audience";

import { PageHeader } from "../../../_components/page-header";
import { AudienceDeleteButton } from "./audience-delete-button";
import { MemberAddDialog } from "./member-add-dialog";
import { MemberImportDialog } from "./member-import-dialog";

export interface AudienceDetailHeaderProps {
  audience: Audience;
}

/** The list's name, what it is used by, and the three things you can do to it. */
export function AudienceDetailHeader({ audience }: AudienceDetailHeaderProps) {
  const used = audience.campaign_count;

  return (
    <div className="space-y-4">
      <Link
        href="/audiences"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeftIcon aria-hidden className="size-4" />
        All audiences
      </Link>

      <PageHeader
        eyebrow={`${formatCount(audience.member_count)} ${audience.member_count === 1 ? "person" : "people"}`}
        title={audience.name}
        description={
          audience.description ??
          (used > 0
            ? `Targeted by ${formatCount(used)} campaign${used === 1 ? "" : "s"}.`
            : "Not targeted by a campaign yet.")
        }
        actions={
          <>
            <MemberImportDialog audienceId={audience.id} />
            <MemberAddDialog audienceId={audience.id} />
            <AudienceDeleteButton audience={audience} />
          </>
        }
      />
    </div>
  );
}
