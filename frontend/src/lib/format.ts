/**
 * Presentation helpers.
 *
 * The API sends raw values - decimals for rates, integer minor units for money,
 * ISO strings for time. Every human-readable form is produced here so the same
 * number never renders two ways in two components.
 */

const DEFAULT_LOCALE = "en-IN";

/** `1234` -> `1,234`. */
export function formatCount(value: number, locale = DEFAULT_LOCALE): string {
  return new Intl.NumberFormat(locale).format(value);
}

/** `0.578` -> `57.8%`. Rates arrive as decimals, never pre-formatted. */
export function formatRate(value: number, locale = DEFAULT_LOCALE, fractionDigits = 1): string {
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

/** `5000000, "INR"` -> `₹50,000`. Minor units in, major units out. */
export function formatMoneyMinor(
  amountMinor: number,
  currency: string,
  locale = DEFAULT_LOCALE,
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amountMinor / 100);
}

/** `2026-08-25T09:00:00Z` -> `25 Aug 2026`. */
export function formatDate(iso: string, timeZone?: string, locale = DEFAULT_LOCALE): string {
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone,
  }).format(new Date(iso));
}

/** `2026-08-25T09:00:00Z` -> `25 Aug 2026, 2:30 pm`. */
export function formatDateTime(iso: string, timeZone?: string, locale = DEFAULT_LOCALE): string {
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone,
  }).format(new Date(iso));
}

/**
 * `25 Aug - 25 Sep 2026`, or `From 25 Aug 2026` when the campaign has no end.
 * A campaign with neither bound reads as "Always on".
 */
export function formatDateRange(
  startIso: string | null,
  endIso: string | null,
  timeZone?: string,
  locale = DEFAULT_LOCALE,
): string {
  if (!startIso && !endIso) return "Always on";
  if (!startIso) return `Until ${formatDate(endIso as string, timeZone, locale)}`;
  if (!endIso) return `From ${formatDate(startIso, timeZone, locale)}`;
  return `${formatDate(startIso, timeZone, locale)} – ${formatDate(endIso, timeZone, locale)}`;
}

/** `42` -> `0:42`, `128` -> `2:08`. */
export function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

const BYTE_UNITS = ["B", "KB", "MB", "GB"] as const;

/** `209715200` -> `200 MB`. Binary steps, the unit a file manager shows. */
export function formatBytes(bytes: number, locale = DEFAULT_LOCALE): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";

  const step = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), BYTE_UNITS.length - 1);
  const value = bytes / 1024 ** step;

  return `${new Intl.NumberFormat(locale, {
    // Whole bytes and kilobytes; a decimal only where it carries meaning.
    maximumFractionDigits: step < 2 ? 0 : 1,
  }).format(value)} ${BYTE_UNITS[step]}`;
}
