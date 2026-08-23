/**
 * The campaign form's six sections, and the map from an error to the section
 * that holds it.
 *
 * Progressive disclosure has a failure mode: an error on a field inside a
 * collapsed section is an error nobody can see. So every field path resolves
 * to a section, and the form opens the ones that need attention before it
 * reports anything.
 *
 * The creative is not here. Ads are a separate screen with their own flat
 * form - see `ad-form.tsx`.
 */

export type BuilderSectionId =
  "campaign" | "schedule" | "audience" | "compliance" | "delivery" | "tracking";

export interface BuilderSection {
  id: BuilderSectionId;
  title: string;
  description: string;
  /** 1 is the brief's mandatory set; 3 is the first thing to cut. */
  tier: 1 | 2 | 3;
}

export const BUILDER_SECTIONS: BuilderSection[] = [
  {
    id: "campaign",
    title: "Campaign",
    description: "What this campaign is called and what it is for.",
    tier: 1,
  },
  {
    id: "audience",
    title: "Audience",
    description: "Who receives it. The name here resolves {{customer_name}}.",
    tier: 1,
  },
  {
    id: "schedule",
    title: "Schedule",
    description: "When the campaign runs. Leave blank to go live on publish.",
    tier: 2,
  },
  {
    id: "compliance",
    title: "Compliance",
    description: "Special category and the disclaimer shown under the video.",
    tier: 2,
  },
  {
    id: "delivery",
    title: "Budget & delivery",
    description: "Spend limits, send caps and pacing.",
    tier: 3,
  },
  {
    id: "tracking",
    title: "Tracking",
    description: "UTM parameters appended to follow-up links.",
    tier: 3,
  },
];

/** Tier 1 is open on arrival; the rest stay folded until they are needed. */
export const DEFAULT_OPEN_SECTIONS: BuilderSectionId[] = BUILDER_SECTIONS.filter(
  (section) => section.tier === 1,
).map((section) => section.id);

/** Which section a dotted field path lives in. */
export function sectionForField(field: string): BuilderSectionId {
  if (field.startsWith("schedule.")) return "schedule";
  if (field === "audience_id") return "audience";
  if (field.startsWith("compliance.")) return "compliance";
  if (field.startsWith("budget.") || field.startsWith("delivery.")) return "delivery";
  if (field.startsWith("tracking.")) return "tracking";
  return "campaign";
}

const FIELD_LABELS: Record<string, string> = {
  name: "Campaign name",
  description: "Description",
  objective: "Objective",
  "schedule.start_at": "Start",
  "schedule.end_at": "End",
  "schedule.timezone": "Timezone",
  audience_id: "Audience",
  ads: "Ads",
  "compliance.disclaimer_text": "Disclaimer",
  "budget.budget_amount_minor": "Budget amount",
  "budget.spend_cap_minor": "Spend cap",
  "delivery.send_cap_per_day": "Daily send cap",
  "delivery.pacing": "Pacing",
};

/** A human name for a field path, including the per-ad ones. */
export function describeField(field: string): string {
  const known = FIELD_LABELS[field];
  if (known) return known;

  // Publishing reports blockers on the campaign's ads, which this form does
  // not contain - they are named so the checklist can point at the Ads tab.
  const ad = /^ads\.(\d+)\.(.+)$/.exec(field);
  if (ad) {
    const index = Number.parseInt(ad[1], 10) + 1;
    const option = /^options\.(\d+)\.(\w+)$/.exec(ad[2]);
    const part = option
      ? `option ${option[1]} ${option[2].replace(/_/g, " ")}`
      : ad[2].replace(/_/g, " ");
    return `Ad ${index}: ${part}`;
  }

  return field;
}
