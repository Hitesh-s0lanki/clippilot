/**
 * The audience: a reusable, named list of people that campaigns select.
 *
 * Owned by the account rather than by one campaign, which is what lets the
 * same list run several of them. Mirrors `backend/src/schemas/audience.py`.
 */

export type Gender = "FEMALE" | "MALE" | "OTHER" | "UNKNOWN";

export type AgeGroup =
  | "UNDER_18"
  | "AGE_18_24"
  | "AGE_25_34"
  | "AGE_35_44"
  | "AGE_45_54"
  | "AGE_55_64"
  | "AGE_65_PLUS"
  | "UNKNOWN";

/**
 * One person.
 *
 * Only `full_name` is ever guaranteed. Everything else is nullable because an
 * uploaded list is ragged, and the screens have to render a row that is a name
 * and nothing else.
 */
export interface AudienceMember {
  id: string;
  /** Resolves `{{customer_name}}` in campaign copy. */
  full_name: string;
  email: string | null;
  phone: string | null;
  age: number | null;
  /** Derived server-side from `age`, so it cannot go stale on a birthday. */
  age_group: AgeGroup;
  gender: Gender;
  city: string | null;
  country: string | null;
  /** CRM contact id. */
  external_ref: string | null;
  attributes: Record<string, string> | null;
  created_at: string;
}

export interface AudienceMemberPage {
  items: AudienceMember[];
  /** Counts what matched the filter, not the whole list. */
  total: number;
  limit: number;
  offset: number;
}

/** One slice of a breakdown. `key` is an enum value, or the place itself. */
export interface SegmentBucket {
  key: string;
  count: number;
  /** Fraction of the whole audience, 0-1. */
  share: number;
}

/** What the audience is made of, without naming anybody. */
export interface AudienceSegments {
  total: number;
  with_email: number;
  with_phone: number;
  age_groups: SegmentBucket[];
  genders: SegmentBucket[];
  cities: SegmentBucket[];
  countries: SegmentBucket[];
}

export interface AudienceSummary {
  id: string;
  name: string;
  description: string | null;
  member_count: number;
  /** Campaigns currently pointing at this audience. Blocks deletion when > 0. */
  campaign_count: number;
  created_at: string;
  updated_at: string;
}

/** One audience with its breakdown. Members come from the members endpoint. */
export interface Audience extends AudienceSummary {
  segments: AudienceSegments;
}

/**
 * What a campaign says about the list it targets.
 *
 * Deliberately thinner than {@link AudienceSummary}: a campaign read carries
 * only enough to name the list and say how big it is. Everything else about
 * the audience is fetched from the audience itself.
 */
export interface AudienceSelection {
  id: string;
  name: string;
  member_count: number;
}

export interface AudiencePage {
  items: AudienceSummary[];
  total: number;
  limit: number;
  offset: number;
}

/* -------------------------------------------------------------------------
 * Write payloads
 * ---------------------------------------------------------------------- */

/**
 * One person as the API accepts them.
 *
 * Every field but the name is optional, and that is the contract the CSV
 * importer is built against: a file with one column still uploads.
 */
export interface AudienceMemberInput {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  age?: number | null;
  gender?: Gender;
  city?: string | null;
  country?: string | null;
  external_ref?: string | null;
}

export interface AudienceWritePayload {
  name: string;
  description?: string | null;
  members?: AudienceMemberInput[];
}

export type AudienceUpdatePayload = Partial<Pick<AudienceWritePayload, "name" | "description">>;

/** One row that did not land, and why. */
export interface SkippedMember {
  index: number;
  full_name: string;
  reason: string;
}

/**
 * The outcome of a bulk add.
 *
 * A partial success is the normal case: one repeated email costs its row, not
 * the file, and every row that did not land is named.
 */
export interface AudienceImportResult {
  added: number;
  skipped: SkippedMember[];
  /** Size of the audience after the import. */
  member_count: number;
}

/* -------------------------------------------------------------------------
 * Labels
 *
 * The API stores enum values and the UI owns the words, the same split the
 * CTA and status enums use.
 * ---------------------------------------------------------------------- */

export const AGE_GROUP_LABELS: Record<AgeGroup, string> = {
  UNDER_18: "Under 18",
  AGE_18_24: "18–24",
  AGE_25_34: "25–34",
  AGE_35_44: "35–44",
  AGE_45_54: "45–54",
  AGE_55_64: "55–64",
  AGE_65_PLUS: "65+",
  UNKNOWN: "Not given",
};

/** The order a breakdown reads in, which is by age and not by size. */
export const AGE_GROUP_ORDER: AgeGroup[] = [
  "UNDER_18",
  "AGE_18_24",
  "AGE_25_34",
  "AGE_35_44",
  "AGE_45_54",
  "AGE_55_64",
  "AGE_65_PLUS",
  "UNKNOWN",
];

export const GENDER_LABELS: Record<Gender, string> = {
  FEMALE: "Female",
  MALE: "Male",
  OTHER: "Other",
  UNKNOWN: "Not given",
};

export const GENDER_ORDER: Gender[] = ["FEMALE", "MALE", "OTHER", "UNKNOWN"];

/** Label a bucket key, falling back to the key for cities and countries. */
export function segmentLabel(key: string): string {
  return (
    AGE_GROUP_LABELS[key as AgeGroup] ??
    GENDER_LABELS[key as Gender] ??
    (key === "UNKNOWN" ? "Not given" : key)
  );
}
