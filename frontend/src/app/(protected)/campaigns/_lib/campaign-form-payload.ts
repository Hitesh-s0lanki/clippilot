import type { CampaignWritePayload, OptionInput, RecipientInput } from "@/types/campaign";

import type {
  CampaignFormValues,
  OptionFormValues,
  RecipientFormValues,
} from "./campaign-form-values";
import { fromScheduleInput } from "./schedule";

/**
 * Form state -> the wire format.
 *
 * The one place that knows the API's shape rules, so no component has to:
 * empty strings become `null` (an empty `email` fails validation, a missing one
 * does not), money becomes integer minor units, and the follow-up field that
 * does not match the chosen type is dropped rather than sent - the API rejects
 * a payload that carries both.
 */

function text(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function count(value: string): number | null {
  const parsed = Number.parseInt(value.trim(), 10);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Major units as typed -> integer minor units. `50000` -> `5000000`. */
export function toMinorUnits(value: string): number | null {
  const parsed = Number.parseFloat(value.trim());
  return Number.isFinite(parsed) ? Math.round(parsed * 100) : null;
}

function toOptionInput(option: OptionFormValues): OptionInput {
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

function toRecipientInput(recipient: RecipientFormValues): RecipientInput {
  return {
    customer_name: recipient.customer_name.trim(),
    email: text(recipient.email),
    phone: text(recipient.phone),
    external_ref: text(recipient.external_ref),
  };
}

export function formToPayload(values: CampaignFormValues): CampaignWritePayload {
  // A single-recipient campaign is rejected server-side if it carries two, and
  // rows the user left completely blank are not recipients at all.
  const filled = values.recipients.filter((recipient) => recipient.customer_name.trim().length > 0);
  const recipients = values.audience_type === "SINGLE" ? filled.slice(0, 1) : filled;

  const budgetType = values.budget_type;

  return {
    name: values.name.trim(),
    description: text(values.description),
    objective: values.objective,
    audience_type: values.audience_type,

    schedule: {
      start_at: fromScheduleInput(values.start_at),
      end_at: fromScheduleInput(values.end_at),
      timezone: values.timezone || "UTC",
    },

    budget: {
      budget_type: budgetType,
      budget_amount_minor: budgetType === "NONE" ? null : toMinorUnits(values.budget_amount),
      currency: values.currency.toUpperCase(),
      spend_cap_minor: budgetType === "NONE" ? null : toMinorUnits(values.spend_cap),
    },

    delivery: {
      pacing: values.pacing,
      send_cap_total: count(values.send_cap_total),
      send_cap_per_day: count(values.send_cap_per_day),
      frequency_cap_per_recipient: count(values.frequency_cap_per_recipient) ?? 1,
    },

    compliance: {
      special_category: values.special_category,
      disclaimer_text: values.special_category === "NONE" ? null : text(values.disclaimer_text),
    },

    tracking: {
      utm_source: text(values.utm_source),
      utm_medium: text(values.utm_medium),
      utm_campaign: text(values.utm_campaign),
      utm_content: text(values.utm_content),
      external_ref: text(values.external_ref),
    },

    experience: {
      video_url: text(values.video_url),
      poster_url: text(values.poster_url),
      headline: text(values.headline),
      personalised_message: text(values.personalised_message),
      options: values.options.map(toOptionInput),
    },

    recipients: recipients.map(toRecipientInput),
  };
}
