import { MAX_ADS_PER_CAMPAIGN, type AdInput, type CampaignWritePayload } from "@/types/campaign";
import type { CampaignStrategy } from "@/types/agent";

/**
 * A generated strategy -> the body of `POST /campaigns`.
 *
 * The draft is deliberately not spread wholesale. `CampaignCreate` forbids
 * unknown keys and requires a name, and the agent may legitimately leave any
 * field null - so every block is copied only when the agent filled it in, and
 * the API's own defaults cover the rest.
 *
 * Two things the agent cannot supply are added here:
 *
 * - `audience_id`, because it has no idea which of your lists to target;
 * - nothing for `video_url`, because it writes the concept and you record the
 *   video. The ads therefore arrive incomplete on purpose, and land as drafts
 *   for you to finish rather than as creatives pretending to be ready.
 */
export function strategyToPayload(
  strategy: CampaignStrategy,
  audienceId: string,
): CampaignWritePayload {
  const draft = strategy.campaign;

  const payload: CampaignWritePayload = {
    // The agent is asked for a name and normally gives one; the business name
    // is a better fallback than "Untitled", which nobody can find later.
    name: draft.name?.trim() || strategy.business.name?.trim() || "Generated campaign",
    description: draft.description ?? null,
    objective: draft.objective ?? "ENGAGEMENT",
    audience_id: audienceId,
    schedule: {
      start_at: null,
      end_at: null,
      timezone: draft.schedule?.timezone || "UTC",
    },
    budget: {
      budget_type: draft.budget?.budget_type ?? "NONE",
      budget_amount_minor: draft.budget?.budget_amount_minor ?? null,
      currency: draft.budget?.currency ?? "INR",
      spend_cap_minor: null,
    },
    delivery: {
      pacing: "STANDARD",
      send_cap_total: null,
      send_cap_per_day: null,
      frequency_cap_per_recipient: 1,
    },
    compliance: {
      special_category: draft.compliance?.special_category ?? "NONE",
      disclaimer_text: draft.compliance?.disclaimer_text ?? null,
    },
    tracking: {
      utm_source: draft.tracking?.utm_source ?? "trustvid",
      utm_medium: draft.tracking?.utm_medium ?? "interactive-video",
      utm_campaign: draft.tracking?.utm_campaign ?? null,
      utm_content: draft.tracking?.utm_content ?? null,
      external_ref: null,
    },
    ads: draft.ads.slice(0, MAX_ADS_PER_CAMPAIGN).map(toAdInput),
  };

  return payload;
}

function toAdInput(ad: CampaignStrategy["campaign"]["ads"][number], index: number): AdInput {
  return {
    name: ad.name?.trim() || `Ad ${index + 1}`,
    headline: ad.headline ?? null,
    description: ad.description ?? null,
    cta: ad.cta,
    personalised_message: ad.personalised_message ?? null,
    options: ad.options.map((option) => {
      const isUrl = option.follow_up_type === "URL";
      return {
        position: option.position,
        label: option.label,
        intent: option.intent,
        follow_up_type: option.follow_up_type,
        follow_up_message: isUrl ? null : option.follow_up_message,
        follow_up_url: isUrl ? option.follow_up_url : null,
      };
    }),
  };
}
