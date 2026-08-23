import type { CampaignUpdatePayload, CampaignWritePayload } from "@/types/campaign";

import type { CampaignFormValues } from "./campaign-form-values";
import { fromScheduleInput } from "./schedule";

/**
 * Form state -> the wire format.
 *
 * Campaign fields only. Creatives are their own resource with their own form
 * and their own endpoints - see `ad-form-payload.ts`.
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

export function formToCampaignPayload(values: CampaignFormValues): CampaignUpdatePayload {
  const budgetType = values.budget_type;

  return {
    name: values.name.trim(),
    description: text(values.description),
    objective: values.objective,
    // A reference, not a copy: the list itself is built and edited on its own
    // screen, and several campaigns may point at the same one.
    audience_id: text(values.audience_id),

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
  };
}

/**
 * The body for `POST /campaigns`.
 *
 * Carries no ads. The API accepts them inline, but the builder deliberately
 * does not: a campaign is created first and taken to its ads screen, so the
 * user is never asked to invent a creative before the campaign it belongs to
 * exists.
 */
export function formToCreatePayload(values: CampaignFormValues): CampaignWritePayload {
  return { ...formToCampaignPayload(values), ads: [] } as CampaignWritePayload;
}
