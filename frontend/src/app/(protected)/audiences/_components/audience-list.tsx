import { formatCount } from "@/lib/format";
import type { AudienceSummary } from "@/types/audience";

import { AudienceCard } from "./audience-card";

export interface AudienceListProps {
  audiences: AudienceSummary[];
  total: number;
}

/** The grid of lists, with a count so the page says how much it is showing. */
export function AudienceList({ audiences, total }: AudienceListProps) {
  return (
    <section className="space-y-4">
      <h2 className="text-sm font-medium text-muted-foreground">
        {formatCount(total)} audience{total === 1 ? "" : "s"}
      </h2>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {audiences.map((audience) => (
          <li key={audience.id} className="flex">
            <AudienceCard audience={audience} />
          </li>
        ))}
      </ul>
    </section>
  );
}
