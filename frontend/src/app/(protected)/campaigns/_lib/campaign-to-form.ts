import type { Campaign } from "@/types/campaign";

import { emptyCampaignForm, type CampaignFormValues } from "./campaign-form-values";
import { toScheduleInput } from "./schedule";

/** Minor units back to the major units a person types: `5000000` -> `50000`. */
function toMajorUnits(minor: number | null): string {
  return minor === null ? "" : String(minor / 100);
}

/**
 * An existing campaign, flattened into form state.
 *
 * Built on top of a blank form rather than field by field, so a campaign saved
 * before a field existed - or one whose `ads` is still empty because nobody
 * has opened the builder yet - lands on the same defaults a new campaign
 * would rather than on `undefined`.
 *
 * Campaign settings only. Its creatives are a separate resource with a form of
 * their own, so nothing about them is read here.
 */
export function campaignToForm(campaign: Campaign): CampaignFormValues {
  const blank = emptyCampaignForm(campaign.schedule.timezone);

  return {
    ...blank,
    name: campaign.name,
    description: campaign.description ?? "",
    objective: campaign.objective,

    start_at: toScheduleInput(campaign.schedule.start_at),
    end_at: toScheduleInput(campaign.schedule.end_at),
    timezone: campaign.schedule.timezone,

    audience_id: campaign.audience?.id ?? "",

    special_category: campaign.compliance.special_category,
    disclaimer_text: campaign.compliance.disclaimer_text ?? "",

    budget_type: campaign.budget.budget_type,
    budget_amount: toMajorUnits(campaign.budget.budget_amount_minor),
    currency: campaign.budget.currency,
    spend_cap: toMajorUnits(campaign.budget.spend_cap_minor),
    pacing: campaign.delivery.pacing,
    send_cap_total: campaign.delivery.send_cap_total?.toString() ?? "",
    send_cap_per_day: campaign.delivery.send_cap_per_day?.toString() ?? "",
    frequency_cap_per_recipient: String(campaign.delivery.frequency_cap_per_recipient ?? 1),

    utm_source: campaign.tracking.utm_source ?? "",
    utm_medium: campaign.tracking.utm_medium ?? "",
    utm_campaign: campaign.tracking.utm_campaign ?? "",
    utm_content: campaign.tracking.utm_content ?? "",
    external_ref: campaign.tracking.external_ref ?? "",
  };
}
