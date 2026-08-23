/**
 * Wire types for the campaign strategist.
 *
 * The agent researches a business and its competitors and returns a campaign
 * draft plus the analysis behind it. The draft maps onto `CampaignWritePayload`
 * field for field, with two deliberate gaps:
 *
 * - **no `audience_id`** — the agent has no idea which of your lists to target;
 * - **no `video_url` on any ad** — it writes the concept, you record the video.
 *
 * So a generated campaign lands as a draft with its creatives unfinished, which
 * is the honest outcome rather than one pretending to be ready to publish.
 */

import type {
  CallToAction,
  CampaignObjective,
  FollowUpType,
  OptionIntent,
  SpecialCategory,
} from "./campaign";

export type Confidence = "HIGH" | "MEDIUM" | "LOW";

/* -------------------------------------------------------------------------
 * The brief the user submits
 * ---------------------------------------------------------------------- */

export interface CampaignBrief {
  /** What the user wants, in their own words. The only required field. */
  requirements: string;
  website_url?: string | null;
  competitor_urls?: string[];
  business_name?: string | null;
  industry?: string | null;
  audience_note?: string | null;
  objective?: CampaignObjective | null;
  /** Country or region. Drives currency, timezone and compliance. */
  market?: string | null;
}

/* -------------------------------------------------------------------------
 * The research
 * ---------------------------------------------------------------------- */

export interface BusinessProfile {
  name: string | null;
  summary: string;
  industry: string | null;
  value_propositions: string[];
  target_audience: string | null;
  tone_of_voice: string | null;
  primary_call_to_action: string | null;
}

export interface CompetitorInsight {
  name: string;
  website_url: string | null;
  positioning: string | null;
  ad_angles: string[];
  /** Actual headlines observed, quoted. */
  hooks: string[];
  /** What they are *not* saying. Where the recommendation comes from. */
  gap: string | null;
}

export interface CreativeDirection {
  angle: string;
  why_it_wins: string;
  video_concept: string;
  opening_hook: string | null;
  proof_points: string[];
  avoid: string[];
}

export interface FieldRationale {
  /** Dotted path into the draft, e.g. `ads.0.options.0.label`. */
  field: string;
  reason: string;
  confidence: Confidence;
}

export interface ResearchSource {
  url: string;
  title: string | null;
  used_for: string | null;
}

/* -------------------------------------------------------------------------
 * The draft
 * ---------------------------------------------------------------------- */

export interface DraftOption {
  position: number;
  label: string;
  intent: OptionIntent;
  follow_up_type: FollowUpType;
  follow_up_message: string | null;
  follow_up_url: string | null;
}

export interface DraftAd {
  name: string;
  headline: string | null;
  description: string | null;
  cta: CallToAction;
  personalised_message: string | null;
  options: DraftOption[];
}

export interface CampaignDraft {
  name: string | null;
  description: string | null;
  objective: CampaignObjective | null;
  schedule: { timezone: string } | null;
  budget: {
    budget_type: "NONE" | "DAILY" | "LIFETIME";
    budget_amount_minor: number | null;
    currency: string;
  } | null;
  compliance: {
    special_category: SpecialCategory;
    disclaimer_text: string | null;
  } | null;
  tracking: {
    utm_source: string | null;
    utm_medium: string | null;
    utm_campaign: string | null;
    utm_content: string | null;
  } | null;
  ads: DraftAd[];
}

export interface CampaignStrategy {
  /** False when the agent worked from the brief alone. */
  researched: boolean;
  business: BusinessProfile;
  competitors: CompetitorInsight[];
  creative: CreativeDirection;
  campaign: CampaignDraft;
  rationale: FieldRationale[];
  open_questions: string[];
  sources: ResearchSource[];
}

/* -------------------------------------------------------------------------
 * The envelope
 * ---------------------------------------------------------------------- */

export interface AgentRunMeta {
  agent: string;
  model: string;
  steps: number;
  duration_ms: number;
  usage: { input_tokens: number; output_tokens: number; total_tokens: number };
  tool_calls: { step: number; tool: string; ok: boolean; duration_ms: number }[];
  /** True when the agent finished without everything it asked for. */
  degraded: boolean;
  /** Why it was degraded. Surface these - they change trust in the result. */
  notes: string[];
}

export interface CampaignStrategyResponse {
  meta: AgentRunMeta;
  strategy: CampaignStrategy;
}

export interface AgentInfo {
  name: string;
  title: string;
  description: string;
  toolsets: string[];
  /** The subset this deployment can reach. A shortfall means degraded runs. */
  available_toolsets: string[];
}

export interface AgentCatalogue {
  /** False when the server has no model key. Hide the feature rather than failing. */
  enabled: boolean;
  agents: AgentInfo[];
}
