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
 */

export type FieldErrors = Record<string, string>;

const VIDEO_SUFFIXES = [".mp4", ".webm", ".mov"];
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_PATTERN = /^\+?[1-9]\d{6,19}$/;

function isHttpsUrl(value: string): boolean {
  try {
    return new URL(value).protocol === "https:";
  } catch {
    return false;
  }
}

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

  if (values.video_url.trim()) {
    const url = values.video_url.trim();
    if (!isHttpsUrl(url)) {
      errors["experience.video_url"] = "The video URL must start with https://";
    } else if (
      !VIDEO_SUFFIXES.some((suffix) => new URL(url).pathname.toLowerCase().endsWith(suffix))
    ) {
      errors["experience.video_url"] = `The URL must end in ${VIDEO_SUFFIXES.join(", ")}.`;
    }
  }

  if (values.poster_url.trim() && !isHttpsUrl(values.poster_url.trim())) {
    errors["experience.poster_url"] = "The poster URL must start with https://";
  }

  for (const option of values.options) {
    const url = option.follow_up_url.trim();
    if (option.follow_up_type === "URL" && url && !isHttpsUrl(url)) {
      errors[`experience.options.${option.position}.follow_up_url`] =
        "The follow-up link must start with https://";
    }
  }

  values.recipients.forEach((recipient, index) => {
    const email = recipient.email.trim();
    if (email && !EMAIL_PATTERN.test(email)) {
      errors[`recipients.${index}.email`] = "Enter a valid email address, or leave it blank.";
    }

    const phone = recipient.phone.trim();
    if (phone && !PHONE_PATTERN.test(phone)) {
      errors[`recipients.${index}.phone`] = "Use digits only, optionally starting with +.";
    }
  });

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

  if (!values.video_url.trim()) {
    errors["experience.video_url"] = "A video URL is required before publishing.";
  }

  if (!values.personalised_message.trim()) {
    errors["experience.personalised_message"] =
      "A personalised message is required before publishing.";
  }

  for (const option of values.options) {
    const prefix = `experience.options.${option.position}`;

    if (!option.label.trim()) {
      errors[`${prefix}.label`] = "A button label is required.";
    }

    if (option.follow_up_type === "URL") {
      if (!option.follow_up_url.trim()) {
        errors[`${prefix}.follow_up_url`] = "A follow-up link is required for this option.";
      }
    } else if (!option.follow_up_message.trim()) {
      errors[`${prefix}.follow_up_message`] = "A follow-up message is required for this option.";
    }
  }

  if (!values.recipients.some((recipient) => recipient.customer_name.trim())) {
    errors["recipients.0.customer_name"] = "At least one recipient is required to publish.";
  }

  if (values.pacing === "ACCELERATED" && !values.end_at) {
    errors["delivery.pacing"] = "Accelerated pacing needs an end date to accelerate through.";
  }

  return errors;
}
