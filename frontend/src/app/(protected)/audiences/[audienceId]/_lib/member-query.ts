import type { ListMembersParams } from "@/lib/api/audiences";
import type { AgeGroup, Gender } from "@/types/audience";
import { AGE_GROUP_ORDER, GENDER_ORDER } from "@/types/audience";

/**
 * The member filter, carried in the URL rather than in component state.
 *
 * Every filter is a real query string, so a segment can be linked to, shared
 * and returned to with the back button - which is the whole point of being
 * able to say "the 25-34s in Mumbai" at all.
 */

export const MEMBERS_PER_PAGE = 25;

/** One `searchParams` value, which Next hands over as a string or an array. */
type Param = string | string[] | undefined;

function one(value: Param): string | undefined {
  const first = Array.isArray(value) ? value[0] : value;
  return first?.trim() || undefined;
}

/** Accept a value only if it is a member of the enum, so a hand-edited URL cannot 422. */
function oneOf<T extends string>(value: Param, allowed: readonly T[]): T | undefined {
  const candidate = one(value);
  return allowed.includes(candidate as T) ? (candidate as T) : undefined;
}

export interface MemberQuery extends ListMembersParams {
  /** 1-based, for the paginator. */
  page: number;
}

/** Read the filter out of the URL. Anything unrecognised is simply not applied. */
export function parseMemberQuery(searchParams: Record<string, Param>): MemberQuery {
  const page = Math.max(1, Number.parseInt(one(searchParams.page) ?? "1", 10) || 1);

  return {
    search: one(searchParams.q),
    city: one(searchParams.city),
    country: one(searchParams.country),
    ageGroup: oneOf<AgeGroup>(searchParams.age, AGE_GROUP_ORDER),
    gender: oneOf<Gender>(searchParams.gender, GENDER_ORDER),
    hasEmail: one(searchParams.reach) === "email" ? true : undefined,
    hasPhone: one(searchParams.reach) === "phone" ? true : undefined,
    limit: MEMBERS_PER_PAGE,
    offset: (page - 1) * MEMBERS_PER_PAGE,
    page,
  };
}

/**
 * The current filter as a query string, for building links off it.
 *
 * A string rather than a `URLSearchParams`: this crosses into components that
 * may render on the client, and only plain values survive that boundary.
 */
export function toQueryString(searchParams: Record<string, Param>): string {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(searchParams)) {
    const single = one(value);
    if (single !== undefined) params.set(key, single);
  }

  return params.toString();
}

/** True when anything is narrowing the list, so the UI can offer "clear". */
export function isFiltered(query: MemberQuery): boolean {
  return Boolean(
    query.search ||
    query.city ||
    query.country ||
    query.ageGroup ||
    query.gender ||
    query.hasEmail ||
    query.hasPhone,
  );
}

/**
 * Build the next URL from the current one.
 *
 * Changing any filter drops `page`: staying on page 4 of a result set that now
 * has one page shows an empty table and reads as "no results".
 */
export function memberHref(
  audienceId: string,
  current: string,
  changes: Record<string, string | undefined>,
): string {
  const next = new URLSearchParams(current);

  for (const [key, value] of Object.entries(changes)) {
    if (value === undefined || value === "") {
      next.delete(key);
    } else {
      next.set(key, value);
    }
  }

  if (!("page" in changes)) next.delete("page");

  const query = next.toString();
  return query ? `/audiences/${audienceId}?${query}` : `/audiences/${audienceId}`;
}
