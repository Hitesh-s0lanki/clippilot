import type { Audience, AudienceMemberPage } from "@/types/audience";

import { MEMBERS_PER_PAGE } from "../_lib/member-query";
import { MemberPagination } from "./member-pagination";
import { MemberTable } from "./member-table";
import { MembersEmptyState } from "./members-empty-state";

export interface MemberPanelProps {
  audience: Audience;
  members: AudienceMemberPage;
  query: string;
  page: number;
  filtered: boolean;
}

/** The table, or the reason there is no table, plus its pager. */
export function MemberPanel({ audience, members, query, page, filtered }: MemberPanelProps) {
  if (members.items.length === 0) {
    return <MembersEmptyState audienceId={audience.id} filtered={filtered} />;
  }

  return (
    <div className="space-y-4">
      <MemberTable audienceId={audience.id} members={members.items} />
      <MemberPagination
        audienceId={audience.id}
        query={query}
        page={page}
        perPage={MEMBERS_PER_PAGE}
        total={members.total}
      />
    </div>
  );
}
