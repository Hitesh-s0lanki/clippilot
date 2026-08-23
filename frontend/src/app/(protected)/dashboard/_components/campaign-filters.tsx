"use client";

import { SearchIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CampaignStatus } from "@/types/campaign";

import { dashboardHref, type DashboardQuery } from "../_lib/dashboard-query";

export interface CampaignFiltersProps {
  query: DashboardQuery;
}

const STATUS_OPTIONS: { value: CampaignStatus | "ALL"; label: string }[] = [
  { value: "ALL", label: "All statuses" },
  { value: "DRAFT", label: "Draft" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "ACTIVE", label: "Active" },
  { value: "PAUSED", label: "Paused" },
  { value: "COMPLETED", label: "Completed" },
  { value: "ARCHIVED", label: "Archived" },
];

const DEBOUNCE_MS = 300;

/**
 * Status and name filters, written to the URL.
 *
 * Navigating rather than filtering in place keeps the server as the one place
 * that decides what the list contains, and makes a filtered dashboard a link
 * someone can send. The search box is debounced so typing does not fire a
 * request per keystroke, and it is a real `<form>` so Enter submits at once
 * instead of waiting out the delay.
 */
export function CampaignFilters({ query }: CampaignFiltersProps) {
  const router = useRouter();
  const [search, setSearch] = useState(query.search);
  const [urlSearch, setUrlSearch] = useState(query.search);

  // Adjusting during render rather than in an effect, which is React's own
  // answer to "a prop changed and this state derives from it". It matters when
  // the URL moves from elsewhere - "Clear filters" in the empty state, or the
  // back button - and it is a no-op when the URL is catching up to what was
  // typed here.
  if (query.search !== urlSearch) {
    setUrlSearch(query.search);
    setSearch(query.search);
  }

  useEffect(() => {
    if (search === query.search) return;

    const timer = setTimeout(() => {
      router.push(dashboardHref({ ...query, search, page: 1 }));
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [search, query, router]);

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    router.push(dashboardHref({ ...query, search, page: 1 }));
  }

  function selectStatus(value: string) {
    const status = value === "ALL" ? undefined : (value as CampaignStatus);
    router.push(dashboardHref({ ...query, status, page: 1 }));
  }

  return (
    <form
      onSubmit={submit}
      // A surface, not a bare row: the filters sit between the summary tiles
      // and the card grid, and without one they read as loose controls floating
      // between two groups of cards rather than as the toolbar for the list.
      className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3 sm:flex-row sm:items-end"
    >
      <div className="flex-1 space-y-1.5">
        <Label htmlFor="campaign-search">Search campaigns</Label>
        <div className="relative">
          <SearchIcon
            aria-hidden
            className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            id="campaign-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by name"
            className="h-9 pl-8"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="campaign-status">Status</Label>
        <Select value={query.status ?? "ALL"} onValueChange={selectStatus}>
          <SelectTrigger id="campaign-status" className="h-9 w-full sm:w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map(({ value, label }) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {query.filtered ? (
        <Button asChild variant="ghost" size="lg" className="sm:mb-px">
          <Link href="/dashboard">
            <XIcon data-icon="inline-start" />
            Clear
          </Link>
        </Button>
      ) : null}
    </form>
  );
}
