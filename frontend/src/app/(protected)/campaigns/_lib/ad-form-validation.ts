import type { AdFormValues } from "./ad-form-values";
import type { FieldErrors } from "./campaign-form-validation";

/**
 * Client-side validation for one ad.
 *
 * Mirrors the API's rules rather than replacing them: the server stays the
 * authority and its rejections merge into the same map, keyed by the same
 * field names, so an error looks identical whichever side produced it.
 *
 * Two contracts, deliberately different. Saving an ad needs only a name -
 * a half-built creative is a legitimate thing to keep. Switching it on runs
 * the full set, which is what `collect_ad_blockers` enforces server-side.
 */

const VIDEO_SUFFIXES = [".mp4", ".webm", ".mov"];

function isHttpsUrl(value: string): boolean {
  try {
    return new URL(value).protocol === "https:";
  } catch {
    return false;
  }
}

/** Rules that apply to any save, because the API rejects them on write. */
export function validateAdDraft(values: AdFormValues): FieldErrors {
  const errors: FieldErrors = {};

  if (!values.name.trim()) {
    errors.name = "An ad name is required, even for a draft.";
  }

  const video = values.video_url.trim();
  if (video) {
    if (!isHttpsUrl(video)) {
      errors.video_url = "The video URL must start with https://";
    } else if (
      !VIDEO_SUFFIXES.some((suffix) => new URL(video).pathname.toLowerCase().endsWith(suffix))
    ) {
      errors.video_url = `The URL must end in ${VIDEO_SUFFIXES.join(", ")}.`;
    }
  }

  if (values.poster_url.trim() && !isHttpsUrl(values.poster_url.trim())) {
    errors.poster_url = "The poster URL must start with https://";
  }

  for (const option of values.options) {
    const url = option.follow_up_url.trim();
    if (option.follow_up_type === "URL" && url && !isHttpsUrl(url)) {
      errors[`options.${option.position}.follow_up_url`] = "The link must start with https://";
    }
  }

  return errors;
}

/** Everything the ad needs before it can be switched on. */
export function validateAdComplete(values: AdFormValues): FieldErrors {
  const errors = validateAdDraft(values);

  if (!values.video_url.trim()) {
    errors.video_url = "A video URL is required before this ad can run.";
  }

  if (!values.personalised_message.trim()) {
    errors.personalised_message = "A personalised message is required before this ad can run.";
  }

  for (const option of values.options) {
    const prefix = `options.${option.position}`;

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

  return errors;
}
