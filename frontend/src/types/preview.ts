/**
 * Recipient-facing preview types.
 *
 * The preview payload is the only response the API serves without a session,
 * so it is an explicit allow-list rather than a trimmed campaign: no owner, no
 * budget, no other recipients, and no follow-up copy for options that have not
 * been clicked - revealing both outcomes up front would let a recipient read
 * the response they did not choose.
 */

import type { FollowUpType, SpecialCategory } from "./campaign";

export interface PreviewOption {
  id: string;
  position: number;
  key: string;
  label: string;
}

export interface PreviewExperience {
  id: string;
  video_url: string;
  poster_url: string | null;
  captions_url: string | null;
  headline: string | null;
  /** Already resolved - `{{customer_name}}` is substituted server-side. */
  personalised_message: string;
  options: PreviewOption[];
}

export interface PreviewCompliance {
  special_category: SpecialCategory;
  disclaimer_text: string | null;
}

export interface CampaignPreview {
  campaign_id: string;
  campaign_name: string;
  /** Falls back to `there` when the recipient has no name. */
  customer_name: string;
  recipient_id: string | null;
  experience: PreviewExperience;
  compliance: PreviewCompliance;
  /** Variables the resolver could not fill; left literal, never blanked. */
  unresolved_variables: string[];
}

export type EventType = "VIEW" | "RESPONSE";

export interface PreviewEvent {
  id: string;
  type: EventType;
  session_id: string;
  option_id: string | null;
  occurred_at: string;
  /** `true` when this session had already recorded the event. Not an error. */
  deduplicated: boolean;
}

/** What the preview renders once a response has been recorded. */
export interface ResponseResult {
  event: PreviewEvent;
  follow_up_type: FollowUpType;
  follow_up_message: string | null;
  follow_up_url: string | null;
}

/** The same shape, resolved locally for the owner's own dry-run preview. */
export type FollowUp = Pick<
  ResponseResult,
  "follow_up_type" | "follow_up_message" | "follow_up_url"
>;
