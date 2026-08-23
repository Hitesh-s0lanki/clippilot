import type { CampaignFormValues } from "./campaign-form-values";

/**
 * Form state key -> the API's dotted field path.
 *
 * The form is flat and the wire format is nested, and errors are keyed by the
 * nested path on both sides - the API's validation details and this app's own
 * client rules use the same strings deliberately. This table is the one place
 * the two shapes are reconciled, so editing a field can clear exactly its own
 * error and nothing else.
 */
export const FIELD_PATHS: Record<keyof CampaignFormValues, string> = {
  name: "name",
  description: "description",
  objective: "objective",

  start_at: "schedule.start_at",
  end_at: "schedule.end_at",
  timezone: "schedule.timezone",

  audience_id: "audience_id",

  special_category: "compliance.special_category",
  disclaimer_text: "compliance.disclaimer_text",

  budget_type: "budget.budget_type",
  budget_amount: "budget.budget_amount_minor",
  currency: "budget.currency",
  spend_cap: "budget.spend_cap_minor",
  pacing: "delivery.pacing",
  send_cap_total: "delivery.send_cap_total",
  send_cap_per_day: "delivery.send_cap_per_day",
  frequency_cap_per_recipient: "delivery.frequency_cap_per_recipient",

  utm_source: "tracking.utm_source",
  utm_medium: "tracking.utm_medium",
  utm_campaign: "tracking.utm_campaign",
  utm_content: "tracking.utm_content",
  external_ref: "tracking.external_ref",
};
