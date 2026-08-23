import type { Campaign } from "@/types/campaign";
import type { FollowUp } from "@/types/preview";

import { resolveVariables } from "../../../_lib/personalisation";

/**
 * The follow-ups for a dry run, resolved for one recipient.
 *
 * In the live flow the server returns the follow-up along with the response,
 * after substituting variables. The owner's preview records nothing, so there
 * is no response to carry one - the same substitution is applied here instead,
 * using the same rules, so the two views cannot disagree about what a
 * recipient would read.
 */
export function resolveFollowUps(
  campaign: Campaign,
  customerName: string,
  adId?: string,
): Record<string, FollowUp> {
  const context = { customerName, campaignName: campaign.name };
  // Match the ad the preview is actually rendering. Defaulting to the first
  // would hand back another creative's follow-ups once a campaign has several.
  const ad = campaign.ads.find((candidate) => candidate.id === adId) ?? campaign.ads[0];

  return Object.fromEntries(
    (ad?.options ?? []).map((option) => [
      option.id,
      {
        follow_up_type: option.follow_up_type,
        follow_up_message: option.follow_up_message
          ? resolveVariables(option.follow_up_message, context).text
          : null,
        follow_up_url: option.follow_up_url,
      },
    ]),
  );
}
