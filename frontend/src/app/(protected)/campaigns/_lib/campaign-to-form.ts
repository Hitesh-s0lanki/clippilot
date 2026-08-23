import type { Campaign, FollowUpType } from "@/types/campaign";

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
 * before a field existed - or one whose `experience` is still `null` because
 * nobody has opened the builder yet - lands on the same defaults a new
 * campaign would rather than on `undefined`.
 */
export function campaignToForm(campaign: Campaign): CampaignFormValues {
  const blank = emptyCampaignForm(campaign.schedule.timezone);
  const experience = campaign.experience;

  const options = blank.options.map((fallback) => {
    const saved = experience?.options.find((option) => option.position === fallback.position);
    if (!saved) return fallback;

    return {
      position: saved.position,
      label: saved.label,
      intent: saved.intent,
      follow_up_type: saved.follow_up_type as FollowUpType,
      follow_up_message: saved.follow_up_message ?? "",
      follow_up_url: saved.follow_up_url ?? "",
    };
  });

  const recipients = campaign.audience.recipients.map((recipient) => ({
    customer_name: recipient.customer_name,
    email: recipient.email ?? "",
    phone: recipient.phone ?? "",
    external_ref: recipient.external_ref ?? "",
  }));

  return {
    ...blank,
    name: campaign.name,
    description: campaign.description ?? "",
    objective: campaign.objective,

    start_at: toScheduleInput(campaign.schedule.start_at),
    end_at: toScheduleInput(campaign.schedule.end_at),
    timezone: campaign.schedule.timezone,

    audience_type: campaign.audience.audience_type,
    recipients: recipients.length > 0 ? recipients : blank.recipients,

    video_url: experience?.video_url ?? "",
    poster_url: experience?.poster_url ?? "",
    headline: experience?.headline ?? "",
    personalised_message: experience?.personalised_message ?? "",
    options,

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
