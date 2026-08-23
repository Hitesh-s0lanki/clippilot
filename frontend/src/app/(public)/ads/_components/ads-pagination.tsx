import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { formatCount } from "@/lib/format";

import { PAGE_SIZE, adsHref, type AdsQuery } from "../_lib/ads-query";

export interface AdsPaginationProps {
  query: AdsQuery;
  total: number;
  /** How many cards this page actually returned. */
  shown: number;
}

/**
 * Page controls, rendered as links.
 *
 * Links rather than buttons because each page is a real URL: the back button
 * works and a page deep in the library can be shared. Nothing renders at all
 * when everything already fits on one page.
 */
export function AdsPagination({ query, total, shown }: AdsPaginationProps) {
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (lastPage <= 1) return null;

  const first = query.offset + 1;
  const last = query.offset + shown;

  return (
    <nav
      aria-label="Library pages"
      className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4"
    >
      <p className="text-sm text-muted-foreground">
        Showing <span className="tabular-nums">{formatCount(first)}</span>–
        <span className="tabular-nums">{formatCount(last)}</span> of{" "}
        <span className="tabular-nums">{formatCount(total)}</span>
      </p>

      <div className="flex items-center gap-2">
        {query.page > 1 ? (
          <Button asChild variant="outline" size="sm">
            <Link href={adsHref(query.page - 1)} rel="prev">
              <ChevronLeftIcon data-icon="inline-start" />
              Previous
            </Link>
          </Button>
        ) : (
          <Button variant="outline" size="sm" disabled>
            <ChevronLeftIcon data-icon="inline-start" />
            Previous
          </Button>
        )}

        <span className="text-sm text-muted-foreground tabular-nums">
          {query.page} / {lastPage}
        </span>

        {query.page < lastPage ? (
          <Button asChild variant="outline" size="sm">
            <Link href={adsHref(query.page + 1)} rel="next">
              Next
              <ChevronRightIcon data-icon="inline-end" />
            </Link>
          </Button>
        ) : (
          <Button variant="outline" size="sm" disabled>
            Next
            <ChevronRightIcon data-icon="inline-end" />
          </Button>
        )}
      </div>
    </nav>
  );
}
