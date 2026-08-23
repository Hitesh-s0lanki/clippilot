import type { CampaignStatus } from "@/types/campaign";

/**
 * The dashboard's URL state.
 *
 * Filters live in the query string rather than in component state so a filtered
 * view can be linked, bookmarked and restored by the back button - and so the
 * server can do the filtering instead of shipping every campaign to the client.
 */

export const PAGE_SIZE = 12;

const STATUSES = new Set<string>([
  "DRAFT",
  "SCHEDULED",
  "ACTIVE",
  "PAUSED",
  "COMPLETED",
  "ARCHIVED",
]);

export interface DashboardQuery {
  status?: CampaignStatus;
  search: string;
  page: number;
  offset: number;
  includeArchived: boolean;
  /** True when any filter is applied, so the empty state can say which. */
  filtered: boolean;
}

type RawParams = Record<string, string | string[] | undefined>;

function single(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value)?.trim() ?? "";
}

export function parseDashboardQuery(params: RawParams): DashboardQuery {
  const rawStatus = single(params.status).toUpperCase();
  const status = STATUSES.has(rawStatus) ? (rawStatus as CampaignStatus) : undefined;
  const search = single(params.q).slice(0, 120);

  const parsedPage = Number.parseInt(single(params.page), 10);
  const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;

  // Asking for archived explicitly, or filtering to it, both mean "show them".
  const includeArchived = single(params.archived) === "1" || status === "ARCHIVED";

  return {
    status,
    search,
    page,
    offset: (page - 1) * PAGE_SIZE,
    includeArchived,
    filtered: Boolean(status) || search.length > 0 || includeArchived,
  };
}

/** Builds a dashboard URL, dropping empty values so the query stays readable. */
export function dashboardHref(query: Partial<DashboardQuery>): string {
  const params = new URLSearchParams();
  if (query.status) params.set("status", query.status);
  if (query.search) params.set("q", query.search);
  if (query.includeArchived) params.set("archived", "1");
  if (query.page && query.page > 1) params.set("page", String(query.page));

  const suffix = params.toString();
  return suffix ? `/dashboard?${suffix}` : "/dashboard";
}
