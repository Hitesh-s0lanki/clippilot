/**
 * Human labels for the wire enums.
 *
 * The API sends `SCREAMING_SNAKE_CASE` and the frontend owns the words, so
 * every label lives here rather than being spelled out at each call site -
 * otherwise "Lead capture" and "Lead Capture" both ship.
 */

import { formatCount, formatRate } from "@/lib/format";
import type {
  AdEffectiveStatus,
  AdStatus,
  BudgetType,
  CampaignMetrics,
  CampaignObjective,
  FollowUpType,
  OptionIntent,
  Pacing,
  PrimaryMetric,
  SpecialCategory,
} from "@/types/campaign";

export const OBJECTIVE_LABELS: Record<CampaignObjective, string> = {
  AWARENESS: "Awareness",
  ENGAGEMENT: "Engagement",
  LEAD_CAPTURE: "Lead capture",
  CONVERSION: "Conversion",
  RETENTION: "Retention",
};

/** One line explaining what the objective changes, shown under the selector. */
export const OBJECTIVE_HINTS: Record<CampaignObjective, string> = {
  AWARENESS: "Leads with total views.",
  ENGAGEMENT: "Leads with the interaction rate.",
  LEAD_CAPTURE: "Leads with positive-intent responses.",
  CONVERSION: "Leads with follow-up click-through.",
  RETENTION: "Leads with repeat views.",
};

export const AD_STATUS_LABELS: Record<AdStatus, string> = {
  DRAFT: "Draft",
  ACTIVE: "Live",
  PAUSED: "Paused",
  ARCHIVED: "Archived",
};

/**
 * What an ad is actually doing, in words.
 *
 * `CAMPAIGN_PAUSED` is the one that earns its place: the ad is switched on and
 * finished, and it still shows nothing, because the campaign above it is not
 * running. Labelling that "Live" would be a lie the user cannot debug.
 */
export const AD_EFFECTIVE_STATUS_LABELS: Record<AdEffectiveStatus, string> = {
  INCOMPLETE: "Incomplete",
  DRAFT: "Draft",
  ACTIVE: "Live",
  PAUSED: "Paused",
  ARCHIVED: "Archived",
  CAMPAIGN_PAUSED: "Campaign not live",
};

export const INTENT_LABELS: Record<OptionIntent, string> = {
  POSITIVE: "Positive",
  NEUTRAL: "Neutral",
  NEGATIVE: "Negative",
};

export const FOLLOW_UP_TYPE_LABELS: Record<FollowUpType, string> = {
  MESSAGE: "Message",
  URL: "Link",
};

export const SPECIAL_CATEGORY_LABELS: Record<SpecialCategory, string> = {
  NONE: "None",
  FINANCIAL_PRODUCTS_SERVICES: "Financial products & services",
  CREDIT: "Credit",
  EMPLOYMENT: "Employment",
  HOUSING: "Housing",
};

/** The compliance chip on a card has no room for the full category name. */
export const SPECIAL_CATEGORY_CHIPS: Record<SpecialCategory, string> = {
  NONE: "",
  FINANCIAL_PRODUCTS_SERVICES: "Financial services",
  CREDIT: "Credit",
  EMPLOYMENT: "Employment",
  HOUSING: "Housing",
};

export const BUDGET_TYPE_LABELS: Record<BudgetType, string> = {
  NONE: "No budget",
  DAILY: "Daily",
  LIFETIME: "Lifetime",
};

export const PACING_LABELS: Record<Pacing, string> = {
  STANDARD: "Standard",
  ACCELERATED: "Accelerated",
};

/**
 * The headline number, formatted for what it actually is.
 *
 * `views` is a count; every other primary metric the backend can pick is a
 * `0.0-1.0` rate, so rendering them all the same way would print `0.578 views`
 * in one campaign and `58 %` as `0.578` in the next.
 */
export function formatPrimaryMetric(metric: PrimaryMetric): string {
  return metric.key === "views" ? formatCount(metric.value) : formatRate(metric.value);
}

/** `2,500 people`, and the singular when there is exactly one. */
export function formatMemberCount(count: number): string {
  return `${formatCount(count)} ${count === 1 ? "person" : "people"}`;
}

export interface LeadMetric {
  label: string;
  value: string;
}

/**
 * The number a campaign card leads with.
 *
 * Prefers the server's `primary_metric` when it is there - the analytics
 * endpoint computes it, including the positive-intent rate a card cannot
 * derive on its own. The listing endpoint omits it to keep the query cheap, so
 * the card falls back to the two metrics it does receive.
 */
export function leadMetric(objective: CampaignObjective, metrics: CampaignMetrics): LeadMetric {
  if (metrics.primary_metric) {
    return {
      label: metrics.primary_metric.label,
      value: formatPrimaryMetric(metrics.primary_metric),
    };
  }

  if (objective === "AWARENESS") {
    return { label: "Total views", value: formatCount(metrics.views) };
  }

  return { label: "Interaction rate", value: formatRate(metrics.interaction_rate) };
}
