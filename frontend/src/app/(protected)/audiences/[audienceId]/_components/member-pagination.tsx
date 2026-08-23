import Link from "next/link";

import { Button } from "@/components/ui/button";
import { formatCount } from "@/lib/format";

import { memberHref } from "../_lib/member-query";

export interface MemberPaginationProps {
  audienceId: string;
  query: string;
  page: number;
  perPage: number;
  total: number;
}

/**
 * Previous / next over one filtered list.
 *
 * Links rather than buttons, so a page is a real URL that survives a refresh -
 * and the filter travels with it, because the window is meaningless without
 * the filter that produced it.
 */
export function MemberPagination({
  audienceId,
  query,
  page,
  perPage,
  total,
}: MemberPaginationProps) {
  const pages = Math.max(1, Math.ceil(total / perPage));
  if (pages === 1) return null;

  const first = (page - 1) * perPage + 1;
  const last = Math.min(page * perPage, total);
  const href = (target: number) =>
    memberHref(audienceId, query, { page: target === 1 ? undefined : String(target) });

  return (
    <nav aria-label="Pages of this audience" className="flex items-center justify-between gap-4">
      <p className="text-sm text-muted-foreground tabular-nums">
        {formatCount(first)}–{formatCount(last)} of {formatCount(total)}
      </p>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1} asChild={page > 1}>
          {page > 1 ? <Link href={href(page - 1)}>Previous</Link> : <span>Previous</span>}
        </Button>
        <Button variant="outline" size="sm" disabled={page >= pages} asChild={page < pages}>
          {page < pages ? <Link href={href(page + 1)}>Next</Link> : <span>Next</span>}
        </Button>
      </div>
    </nav>
  );
}
