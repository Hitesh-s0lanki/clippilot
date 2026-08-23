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

export type OptionIntent = "POSITIVE" | "NEGATIVE" | "NEUTRAL";
export type FollowUpType = "MESSAGE" | "URL";
export type SpecialCategory =
  "NONE" | "FINANCIAL_PRODUCTS_SERVICES" | "CREDIT" | "EMPLOYMENT" | "HOUSING";
export type AudienceType = "SINGLE" | "LIST";
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

export interface CampaignRecipient {
  id: string;
  customer_name: string;
  email: string | null;
  phone: string | null;
  external_ref: string | null;
}

export interface CampaignAudience {
  audience_type: AudienceType;
  recipient_count: number;
  recipients: CampaignRecipient[];
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

export interface CampaignExperience {
  id: string;
  video_url: string | null;
  poster_url: string | null;
  captions_url: string | null;
  video_duration_seconds: number | null;
  /** May contain `{{customer_name}}`; resolved server-side for the preview. */
  headline: string | null;
  personalised_message: string | null;
  options: CampaignOption[];
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
  audience: CampaignAudience;
  /** `null` until the campaign has been given a creative. */
  experience: CampaignExperience | null;
  metrics: CampaignMetrics;

  /**
   * Dotted field paths that publishing would reject, e.g.
   * `experience.options.1.label`. Empty means the campaign is publishable.
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
 * endpoint omits recipients, options, description and every configuration
 * block, and hoists the two fields a card actually needs.
 */
export interface CampaignSummary {
  id: string;
  name: string;
  objective: CampaignObjective;
  status: CampaignStatus;
  effective_status: CampaignEffectiveStatus;
  badge: CampaignBadge;
  poster_url: string | null;
  recipient_count: number;
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

export interface RecipientInput {
  customer_name: string;
  email?: string | null;
  phone?: string | null;
  external_ref?: string | null;
}

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

export interface ExperienceInput {
  video_url?: string | null;
  poster_url?: string | null;
  captions_url?: string | null;
  video_duration_seconds?: number | null;
  headline?: string | null;
  personalised_message?: string | null;
  options: OptionInput[];
}

/** Body of `POST /campaigns` and `PATCH /campaigns/{id}`. */
export interface CampaignWritePayload {
  name: string;
  description: string | null;
  objective: CampaignObjective;
  audience_type: AudienceType;
  schedule: CampaignSchedule;
  budget: CampaignBudget;
  delivery: CampaignDelivery;
  compliance: CampaignCompliance;
  tracking: CampaignTracking;
  experience: ExperienceInput;
  recipients: RecipientInput[];
}
