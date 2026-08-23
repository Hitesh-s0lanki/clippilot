/**
 * The ads library's URL state.
 *
 * One number, but it lives in the query string rather than component state for
 * the same reason the dashboard's filters do: a page deep in the library is a
 * real URL that can be linked, bookmarked and restored by the back button.
 */

export const PAGE_SIZE = 12;

export interface AdsQuery {
  page: number;
  offset: number;
}

type RawParams = Record<string, string | string[] | undefined>;

export function parseAdsQuery(params: RawParams): AdsQuery {
  const raw = Array.isArray(params.page) ? params.page[0] : params.page;
  const parsed = Number.parseInt(raw?.trim() ?? "", 10);
  const page = Number.isFinite(parsed) && parsed > 0 ? parsed : 1;

  return { page, offset: (page - 1) * PAGE_SIZE };
}

export function adsHref(page: number): string {
  return page > 1 ? `/ads?page=${page}` : "/ads";
}
