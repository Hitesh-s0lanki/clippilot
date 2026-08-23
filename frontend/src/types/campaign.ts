import type { AudienceSelection } from "./audience";

/**
 * Wire types for the campaign entity.
 *
 * Transcribed from `docs/campaign-data-model.md` (§5 Wire format) and verified
 * against `backend/src/schemas/`. Conventions that hold everywhere:
 *
 * - keys are `snake_case`, matching the API exactly - no client-side remapping;
 * - enums are `SCREAMING_SNAKE_CASE`; human labels belong to the frontend;
 * - timestamps are ISO-8601 UTC strings ending in `Z`;
 * - money is integer minor units plus an explicit currency, never a float;
 * - rates are decimals in `0.0-1.0`, not pre-formatted percentages;
 * - `effective_status`, `badge`, `metrics` and `publish_blockers` are read-only -
 *   sent on GET, rejected on write (the backend forbids unknown keys).
 */

export type CampaignObjective =
  "AWARENESS" | "ENGAGEMENT" | "LEAD_CAPTURE" | "CONVERSION" | "RETENTION";

/** What the user chose. Persisted. */
export type CampaignStatus = "DRAFT" | "SCHEDULED" | "ACTIVE" | "PAUSED" | "COMPLETED" | "ARCHIVED";

/** Derived by the server from status + schedule + completeness. Read-only. */
export type CampaignEffectiveStatus = CampaignStatus | "INCOMPLETE";

/** The brief's two-value badge, derived server-side so both readings hold. */
export type CampaignBadge = "Draft" | "Published";

/** What the user chose for one ad. Persisted, and independent of its campaign. */
export type AdStatus = "DRAFT" | "ACTIVE" | "PAUSED" | "ARCHIVED";

/**
 * Derived from the ad's status, its completeness, and its campaign's status.
 *
 * `CAMPAIGN_PAUSED` is the value that makes the two-level hierarchy legible:
 * the ad is switched on and complete, and it still shows nothing, because the
 * campaign above it is not live.
 */
export type AdEffectiveStatus = AdStatus | "INCOMPLETE" | "CAMPAIGN_PAUSED";

/** The action an ad asks for. Supplies the POSITIVE option's default label. */
export type CallToAction =
  | "LEARN_MORE"
  | "GET_QUOTE"
  | "BOOK_NOW"
  | "SIGN_UP"
  | "CONTACT_US"
  | "GET_OFFER"
  | "SUBSCRIBE"
  | "DOWNLOAD"
  | "APPLY_NOW"
  | "SHOP_NOW";

/** Human labels for the CTA enum. The API stores the value, the UI shows this. */
export const CTA_LABELS: Record<CallToAction, string> = {
  LEARN_MORE: "Learn more",
  GET_QUOTE: "Get a quote",
  BOOK_NOW: "Book now",
  SIGN_UP: "Sign up",
  CONTACT_US: "Contact us",
  GET_OFFER: "Get offer",
  SUBSCRIBE: "Subscribe",
  DOWNLOAD: "Download",
  APPLY_NOW: "Apply now",
  SHOP_NOW: "Shop now",
};

export type OptionIntent = "POSITIVE" | "NEGATIVE" | "NEUTRAL";
export type FollowUpType = "MESSAGE" | "URL";
export type SpecialCategory =
  "NONE" | "FINANCIAL_PRODUCTS_SERVICES" | "CREDIT" | "EMPLOYMENT" | "HOUSING";
export type BudgetType = "NONE" | "DAILY" | "LIFETIME";
export type Pacing = "STANDARD" | "ACCELERATED";

export interface CampaignSchedule {
  start_at: string | null;
  end_at: string | null;
  /** IANA zone, e.g. `Asia/Kolkata`. */
  timezone: string;
}

export interface CampaignBudget {
  budget_type: BudgetType;
  /** Integer minor units - 5000000 is ₹50,000. */
  budget_amount_minor: number | null;
  /** ISO 4217, three letters. */
  currency: string;
  spend_cap_minor: number | null;
}

export interface CampaignDelivery {
  pacing: Pacing;
  send_cap_total: number | null;
  send_cap_per_day: number | null;
  frequency_cap_per_recipient: number;
}

export interface CampaignCompliance {
  special_category: SpecialCategory;
  disclaimer_text: string | null;
}

export interface CampaignTracking {
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  utm_content: string | null;
  external_ref: string | null;
}

export interface CampaignOption {
  id: string;
  /** 1 or 2 - the brief's two response options. */
  position: number;
  key: string;
  label: string;
  intent: OptionIntent;
  follow_up_type: FollowUpType;
  follow_up_message: string | null;
  follow_up_url: string | null;
}

/**
 * One ad - the creative a recipient watches.
 *
 * A campaign owns many. The campaign carries the objective, schedule, budget,
 * audience and compliance; each ad carries one video, its copy, its call to
 * action, its two response options and its own status.
 */
export interface CampaignAd {
  id: string;
  campaign_id: string;
  /** Internal label, unique within the campaign. Never shown to a recipient. */
  name: string;

  status: AdStatus;
  effective_status: AdEffectiveStatus;

  video_url: string | null;
  poster_url: string | null;
  captions_url: string | null;
  video_duration_seconds: number | null;

  /** May contain `{{customer_name}}`; resolved server-side for the preview. */
  headline: string | null;
  /**
   * Supporting line beneath the headline, read by the recipient - unlike
   * `Campaign.description`, which is an internal note.
   */
  description: string | null;
  personalised_message: string | null;
  cta: CallToAction;

  options: CampaignOption[];

  /** What this ad is still missing, e.g. `video_url`. Empty means it can run. */
  blockers: string[];

  created_at: string;
  updated_at: string;
}

/**
 * How many creatives one campaign may hold.
 *
 * Mirrors `MAX_ADS_PER_CAMPAIGN` in `backend/src/schemas/ad.py`, which is the
 * authority. Kept here so the UI can hide the Add button at the ceiling rather
 * than offering a form that can only fail.
 */
export const MAX_ADS_PER_CAMPAIGN = 5;

export interface AdList {
  items: CampaignAd[];
  total: number;
}

/** The metric the objective puts at the top of the analytics view. */
export interface PrimaryMetric {
  key: string;
  label: string;
  value: number;
}

export interface CampaignMetrics {
  views: number;
  interactions: number;
  /** `0` when `views` is `0` - never divide by zero, never render `NaN`. */
  interaction_rate: number;
  /** Only populated by the analytics endpoint; `null` on the list and read. */
  primary_metric: PrimaryMetric | null;
  last_activity_at: string | null;
}

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  objective: CampaignObjective;

  status: CampaignStatus;
  effective_status: CampaignEffectiveStatus;
  badge: CampaignBadge;

  schedule: CampaignSchedule;
  budget: CampaignBudget;
  delivery: CampaignDelivery;
  compliance: CampaignCompliance;
  tracking: CampaignTracking;
  /**
   * The list this campaign targets. `null` until one is selected, or after the
   * selected list is deleted - which leaves the campaign unpublishable rather
   * than deleting it.
   */
  audience: AudienceSelection | null;
  /** Empty until the campaign has been given a creative. */
  ads: CampaignAd[];
  metrics: CampaignMetrics;

  /**
   * Dotted field paths that publishing would reject, e.g.
   * `ads.0.options.1.label`. Empty means the campaign is publishable.
   */
  publish_blockers: string[];

  created_at: string;
  updated_at: string;
  published_at: string | null;
  archived_at: string | null;
}

/**
 * The dashboard row.
 *
 * Deliberately flat and much smaller than {@link Campaign}: the listing
 * endpoint omits the audience, options, description and every configuration
 * block, and hoists the two fields a card actually needs.
 */
export interface CampaignSummary {
  id: string;
  name: string;
  objective: CampaignObjective;
  status: CampaignStatus;
  effective_status: CampaignEffectiveStatus;
  badge: CampaignBadge;
  /** Poster of the campaign's primary ad. */
  poster_url: string | null;
  /** Null until an audience is selected. */
  audience_name: string | null;
  /** People in the selected audience. */
  audience_size: number;
  ad_count: number;
  /** Ads that are switched on and complete. */
  live_ad_count: number;
  metrics: CampaignMetrics;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export interface CampaignPage {
  items: CampaignSummary[];
  total: number;
  limit: number;
  offset: number;
}

/* -------------------------------------------------------------------------
 * Write payloads
 *
 * Separate from the read types on purpose: the backend rejects unknown keys,
 * so echoing a `Campaign` back at it fails on `id`, `badge` and friends.
 * ---------------------------------------------------------------------- */

export interface OptionInput {
  position: number;
  label?: string | null;
  intent: OptionIntent;
  follow_up_type: FollowUpType;
  /** Must be empty when `follow_up_type` is `URL`. */
  follow_up_message?: string | null;
  /** Must be empty when `follow_up_type` is `MESSAGE`. */
  follow_up_url?: string | null;
}

/** Body of `POST /campaigns/{id}/ads`, and of each entry in `CampaignWritePayload.ads`. */
export interface AdInput {
  name: string;
  video_url?: string | null;
  poster_url?: string | null;
  captions_url?: string | null;
  video_duration_seconds?: number | null;
  headline?: string | null;
  description?: string | null;
  personalised_message?: string | null;
  cta?: CallToAction;
  options: OptionInput[];
}

/**
 * Body of `PATCH /campaigns/{id}/ads/{adId}`.
 *
 * `status` is absent on purpose: it moves through the status endpoint, which
 * enforces the legal transitions and the completeness contract.
 */
export type AdUpdatePayload = Partial<AdInput>;

/** Body of `POST /campaigns` and `PATCH /campaigns/{id}`. */
export interface CampaignWritePayload {
  name: string;
  description: string | null;
  objective: CampaignObjective;
  schedule: CampaignSchedule;
  budget: CampaignBudget;
  delivery: CampaignDelivery;
  compliance: CampaignCompliance;
  tracking: CampaignTracking;
  /**
   * The list this campaign targets, by id. A reference, not a copy: audiences
   * are account-level and several campaigns may point at the same one.
   */
  audience_id: string | null;
  /**
   * Ads to create alongside the campaign. Present on `POST /campaigns` only -
   * once a campaign exists its ads are managed through `/campaigns/{id}/ads`,
   * because replacing the whole list by index on every campaign PATCH is a
   * footgun when there are several.
   */
  ads: AdInput[];
}

/** Body of `PATCH /campaigns/{id}`. Never carries `ads`. */
export type CampaignUpdatePayload = Partial<Omit<CampaignWritePayload, "ads">>;
