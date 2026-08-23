/**
 * Schedule input helpers.
 *
 * `datetime-local` has no timezone of its own, so the value has to be anchored
 * to one. This module anchors it to **UTC** rather than to the browser's zone,
 * for a specific reason: the builder is a Client Component that Next.js also
 * renders on the server, and `new Date(iso).getHours()` returns a different
 * number in each place. That is a hydration mismatch on every scheduled
 * campaign. Reading and writing UTC is deterministic in both.
 *
 * The campaign's own `timezone` field stays what the API says it is - a
 * display preference - and is used to render the window back in human terms
 * beneath the fields, which `Intl` does deterministically when the zone is
 * passed explicitly.
 */

/** ISO-8601 UTC -> `2026-08-25T09:00`, the value a `datetime-local` wants. */
export function toScheduleInput(iso: string | null): string {
  if (!iso) return "";

  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";

  return date.toISOString().slice(0, 16);
}

/** `2026-08-25T09:00` -> ISO-8601 UTC, or `null` for an empty field. */
export function fromScheduleInput(value: string): string | null {
  if (!value) return null;

  const date = new Date(`${value}:00Z`);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

/**
 * Zones offered in the builder.
 *
 * A curated list rather than all ~400 IANA zones: this only changes how a
 * schedule is displayed, and a 400-row select is a worse answer to that than a
 * short one covering the regions the product ships in. The device's own zone
 * is added at runtime when it is missing.
 */
export const COMMON_TIMEZONES = [
  "UTC",
  "Asia/Kolkata",
  "Asia/Dubai",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Paris",
  "America/New_York",
  "America/Chicago",
  "America/Los_Angeles",
  "Australia/Sydney",
] as const;

/** The curated list plus `current`, so an unusual saved zone is never dropped. */
export function timezoneOptions(current: string): string[] {
  const zones = new Set<string>(COMMON_TIMEZONES);
  if (current) zones.add(current);
  return [...zones].sort();
}
