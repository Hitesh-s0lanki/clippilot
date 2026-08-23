import type { AdInput, OptionInput } from "@/types/campaign";

import type { AdFormValues, AdOptionFormValues } from "./ad-form-values";

/**
 * Ad form state -> the wire format.
 *
 * Empty strings become `null`, and the follow-up field that does not match the
 * chosen type is dropped rather than sent - the API rejects a payload carrying
 * both.
 */

function text(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function toOptionInput(option: AdOptionFormValues): OptionInput {
  const isUrl = option.follow_up_type === "URL";

  return {
    position: option.position,
    label: text(option.label),
    intent: option.intent,
    follow_up_type: option.follow_up_type,
    follow_up_message: isUrl ? null : text(option.follow_up_message),
    follow_up_url: isUrl ? text(option.follow_up_url) : null,
  };
}

export function adFormToPayload(values: AdFormValues): AdInput {
  return {
    name: values.name.trim(),
    video_url: text(values.video_url),
    poster_url: text(values.poster_url),
    headline: text(values.headline),
    description: text(values.description),
    cta: values.cta,
    personalised_message: text(values.personalised_message),
    options: values.options.map(toOptionInput),
  };
}
