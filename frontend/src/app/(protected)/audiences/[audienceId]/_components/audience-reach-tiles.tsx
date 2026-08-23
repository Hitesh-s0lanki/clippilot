import { AtSignIcon, PhoneIcon, UsersIcon } from "lucide-react";

import { formatCount, formatRate } from "@/lib/format";
import type { AudienceSegments } from "@/types/audience";

import { MetricTile } from "../../../_components/metric-tile";

export interface AudienceReachTilesProps {
  segments: AudienceSegments;
}

/**
 * How big the list is, and how much of it can actually be contacted.
 *
 * Reach is the number that decides whether a list is usable: 400 people of
 * whom 60 have an email is a different asset from 400 who all do, and the
 * total alone hides that completely.
 */
export function AudienceReachTiles({ segments }: AudienceReachTilesProps) {
  const share = (count: number) => (segments.total ? formatRate(count / segments.total) : "—");

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <MetricTile
        label="People"
        value={formatCount(segments.total)}
        icon={UsersIcon}
        emphasis="lead"
      />
      <MetricTile
        label="Reachable by email"
        value={formatCount(segments.with_email)}
        hint={`${share(segments.with_email)} of the list`}
        icon={AtSignIcon}
      />
      <MetricTile
        label="Reachable by phone"
        value={formatCount(segments.with_phone)}
        hint={`${share(segments.with_phone)} of the list`}
        icon={PhoneIcon}
      />
    </div>
  );
}
