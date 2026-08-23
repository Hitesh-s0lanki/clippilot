import type { CampaignFormValues } from "./campaign-form-values";
import { toMinorUnits } from "./campaign-form-payload";

/**
 * Client-side validation.
 *
 * It mirrors the API's rules rather than replacing them: the server stays the
 * authority and its rejections are merged into the same map, keyed by the same
 * dotted paths, so an error looks identical whichever side produced it. What
 * this buys is immediate feedback on blur and one fewer round trip before the
 * builder can say what is missing.
 *
 * Two contracts, deliberately different - a draft may be incomplete, and only
 * publishing enforces the full set. See
 * `backend/src/services/publish_validator.py`.
 *
 * Campaign fields only. Whether a *creative* is complete is checked in
 * `ad-form-validation.ts`; publishing additionally requires at least one
 * finished ad, and that blocker comes back from the server keyed `ads`.
 */

export type FieldErrors = Record<string, string>;

/** Rules that apply to any save, because the API rejects them on write. */
export function validateDraft(values: CampaignFormValues): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.name.trim()) {
    errors.name = "A campaign name is required, even for a draft.";
  }

  const start = values.start_at;
  const end = values.end_at;
  if (start && end && end <= start) {
    errors["schedule.end_at"] = "The end must be after the start.";
  }

  if (values.special_category !== "NONE" && !values.disclaimer_text.trim()) {
    errors["compliance.disclaimer_text"] =
      "A disclaimer is required once a special category is declared.";
  }

  if (values.budget_type !== "NONE") {
    const amount = toMinorUnits(values.budget_amount);
    if (amount === null) {
      errors["budget.budget_amount_minor"] = "Enter an amount, or set the budget type to none.";
    } else {
      const cap = toMinorUnits(values.spend_cap);
      if (cap !== null && cap < amount) {
        errors["budget.spend_cap_minor"] = "The spend cap cannot be below the budget amount.";
      }
    }
  }

  const total = Number.parseInt(values.send_cap_total, 10);
  const perDay = Number.parseInt(values.send_cap_per_day, 10);
  if (Number.isFinite(total) && Number.isFinite(perDay) && perDay > total) {
    errors["delivery.send_cap_per_day"] = "The daily cap cannot exceed the total cap.";
  }

  return errors;
}

/** Everything a draft needs, plus the full publish contract. */
export function validatePublish(values: CampaignFormValues): FieldErrors {
  const errors = validateDraft(values);

  if (!values.audience_id.trim()) {
    errors["audience_id"] = "Select an audience before publishing.";
  }

  if (values.pacing === "ACCELERATED" && !values.end_at) {
    errors["delivery.pacing"] = "Accelerated pacing needs an end date to accelerate through.";
  }

  return errors;
}
