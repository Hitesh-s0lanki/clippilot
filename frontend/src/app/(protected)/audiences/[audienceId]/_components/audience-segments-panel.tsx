import type { AudienceSegments, SegmentBucket } from "@/types/audience";
import { AGE_GROUP_ORDER, GENDER_ORDER } from "@/types/audience";

import { memberHref } from "../_lib/member-query";
import { AudienceReachTiles } from "./audience-reach-tiles";
import { SegmentBreakdown } from "./segment-breakdown";

export interface AudienceSegmentsPanelProps {
  audienceId: string;
  segments: AudienceSegments;
  /** The filter currently applied, so a segment link adds to it rather than replacing it. */
  query: string;
  /** Which slice, if any, is filtering the table right now. */
  active: { age?: string; gender?: string; city?: string; country?: string };
}

/**
 * What the audience is made of - the headline of this screen.
 *
 * Deliberately above the table of names. A list of 100 people tells you
 * nothing you can act on; the same 100 broken down by age, gender and place is
 * what you choose a campaign's targeting from. The names are the detail you
 * drop into afterwards.
 *
 * Age and gender are ordered by their own scale rather than by size, because a
 * reader scans an age chart in age order and a bar chart that jumps 45-54,
 * 18-24, 65+ is unreadable. Places are left in the order the API returns them,
 * which is largest first - there is no natural order for a city.
 */
export function AudienceSegmentsPanel({
  audienceId,
  segments,
  query,
  active,
}: AudienceSegmentsPanelProps) {
  const href = (key: string, value: string) => memberHref(audienceId, query, { [key]: value });

  return (
    <div className="space-y-4">
      <AudienceReachTiles segments={segments} />

      <div className="grid gap-4 lg:grid-cols-2">
        <SegmentBreakdown
          title="Age"
          hint="Derived from each person's age, so it never goes stale."
          buckets={inOrder(segments.age_groups, AGE_GROUP_ORDER)}
          hrefFor={(key) => href("age", key)}
          activeKey={active.age}
          emptyLabel="Nobody on this list has an age yet."
        />
        <SegmentBreakdown
          title="Gender"
          buckets={inOrder(segments.genders, GENDER_ORDER)}
          hrefFor={(key) => href("gender", key)}
          activeKey={active.gender}
          emptyLabel="Nobody on this list has a gender yet."
        />
        <SegmentBreakdown
          title="City"
          hint="The eight largest. Smaller cities are still in the list."
          buckets={segments.cities}
          hrefFor={(key) => href("city", key)}
          activeKey={active.city}
          emptyLabel="Nobody on this list has a city yet."
        />
        <SegmentBreakdown
          title="Country"
          buckets={segments.countries}
          hrefFor={(key) => href("country", key)}
          activeKey={active.country}
          emptyLabel="Nobody on this list has a country yet."
        />
      </div>
    </div>
  );
}

/** Sort buckets onto a fixed scale, leaving anything unrecognised at the end. */
function inOrder(buckets: SegmentBucket[], order: readonly string[]): SegmentBucket[] {
  const rank = (key: string) => {
    const at = order.indexOf(key);
    return at === -1 ? order.length : at;
  };

  return [...buckets].sort((a, b) => rank(a.key) - rank(b.key));
}
