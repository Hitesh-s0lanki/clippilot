import { SearchIcon, XIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatCount } from "@/lib/format";
import { segmentLabel } from "@/types/audience";

import type { MemberQuery } from "../_lib/member-query";
import { memberHref } from "../_lib/member-query";

export interface MemberFiltersProps {
  audienceId: string;
  query: MemberQuery;
  /** The filter as a query string, so links can add to it rather than replace it. */
  queryString: string;
  /** How many people matched, so the heading describes the segment on screen. */
  matched: number;
  filtered: boolean;
}

/**
 * Search across the list, and a chip for whatever is narrowing it.
 *
 * A plain GET form and a row of links - no client component, no state. The
 * filter already lives in the URL, so submitting the form *is* the state
 * update, and a debounced input mirroring the URL into React state would only
 * be a second copy of the truth to keep in sync.
 *
 * The active filters read as removable chips rather than a second row of
 * selects: most of them are set by clicking a bar in the breakdown above, so
 * what the user needs next is to see what they picked and be able to undo it,
 * not a control that duplicates the chart.
 */
export function MemberFilters({
  audienceId,
  query,
  queryString,
  matched,
  filtered,
}: MemberFiltersProps) {
  const chips = [
    { key: "age", value: query.ageGroup as string | undefined },
    { key: "gender", value: query.gender as string | undefined },
    { key: "city", value: query.city },
    { key: "country", value: query.country },
    { key: "reach", value: query.hasEmail ? "email" : query.hasPhone ? "phone" : undefined },
  ].filter((chip): chip is { key: string; value: string } => Boolean(chip.value));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-heading text-lg font-semibold tracking-tight">
          {filtered
            ? `${formatCount(matched)} matching`
            : `${formatCount(matched)} ${matched === 1 ? "person" : "people"}`}
        </h2>

        <form action={`/audiences/${audienceId}`} className="relative w-full sm:w-72">
          {/* The other filters ride along as hidden fields, so searching
              inside a segment narrows it rather than leaving it. */}
          {chips.map((chip) => (
            <input key={chip.key} type="hidden" name={chip.key} value={chip.value} />
          ))}
          <Label htmlFor="member-search" className="sr-only">
            Search this audience
          </Label>
          <SearchIcon
            aria-hidden
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            id="member-search"
            name="q"
            type="search"
            defaultValue={query.search ?? ""}
            placeholder="Name, email, phone or CRM ref"
            className="pl-9"
          />
        </form>
      </div>

      {chips.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          {chips.map((chip) => (
            <Link
              key={chip.key}
              href={memberHref(audienceId, queryString, { [chip.key]: undefined })}
              className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 py-1 pr-2 pl-3 text-xs font-medium text-primary hover:bg-primary/15"
            >
              {chip.key === "reach" ? `Has ${chip.value}` : segmentLabel(chip.value)}
              <XIcon aria-hidden className="size-3.5" />
              <span className="sr-only">Remove this filter</span>
            </Link>
          ))}
          <Button variant="ghost" size="sm" asChild>
            <Link href={`/audiences/${audienceId}`}>Clear all</Link>
          </Button>
        </div>
      ) : null}
    </div>
  );
}
