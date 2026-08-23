/**
 * The public ads library.
 *
 * Wire types for `GET /public/campaigns` - the widest unauthenticated surface
 * the API has, since it needs no campaign id to reach. The payload is a
 * thinner allow-list than the preview: the server renders it with no recipient
 * bound, so `{{customer_name}}` resolves to its fallback and nothing that
 * identifies a customer can appear here.
 */

import type { CampaignObjective, SpecialCategory } from "./campaign";

/**
 * One live **ad**, not one campaign.
 *
 * A campaign can hold several creatives, and each live one gets its own card -
 * a single card per campaign would silently hide all but the first.
 */
export interface PublicCampaignCard {
  campaign_id: string;
  campaign_name: string;
  ad_id: string;
  /** Internal label. Shown only as a fallback when the ad has no headline. */
  ad_name: string;
  objective: CampaignObjective;
  headline: string | null;
  /** Already resolved, with no recipient - reads "Hi there, ...". */
  preview_message: string;
  poster_url: string | null;
  video_duration_seconds: number | null;
  special_category: SpecialCategory;
  /** Both response buttons, in the order the recipient sees them. */
  option_labels: string[];
  published_at: string | null;
}

export interface PublicCampaignPage {
  items: PublicCampaignCard[];
  total: number;
  limit: number;
  offset: number;
}
