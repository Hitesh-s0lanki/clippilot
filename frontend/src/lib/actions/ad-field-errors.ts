import { isApiError } from "@/lib/api/errors";
import type { ActionResult } from "@/types/action";

/**
 * Mapping an ad's failures onto the campaign form's field paths.
 *
 * Deliberately *not* a `"use server"` module: these are pure functions, and a
 * Server Actions file may only export async ones. Keeping them here lets both
 * `ad-actions` and `campaign-actions` use them.
 *
 * The re-keying is the point. The ad endpoints key their validation details to
 * the ad's own field names — `video_url`, `options.1.label` — because they know
 * nothing about the campaign form. The builder keys its errors by the
 * campaign-level path, `ads.0.video_url`. Every failure crossing that boundary
 * is re-keyed, or an error arrives for a field the form cannot find and the
 * user sees "something went wrong" next to no field at all.
 */
export function prefixAdErrors(
  fieldErrors: Record<string, string>,
  index = 0,
): Record<string, string> {
  return Object.fromEntries(
    Object.entries(fieldErrors).map(([field, message]) => [`ads.${index}.${field}`, message]),
  );
}

/** An ad failure as an ActionResult, optionally re-keyed onto `ads.{index}.*`. */
export function toAdFailure(error: unknown, index?: number): Extract<ActionResult, { ok: false }> {
  if (isApiError(error)) {
    const fieldErrors = error.fieldErrors();
    return {
      ok: false,
      code: error.code,
      message: error.message,
      fieldErrors: index === undefined ? fieldErrors : prefixAdErrors(fieldErrors, index),
    };
  }

  return {
    ok: false,
    code: "UNEXPECTED_ERROR",
    message: "Something went wrong. Try again.",
    fieldErrors: {},
  };
}
