import { AlertTriangleIcon, CheckCircle2Icon } from "lucide-react";

import type { CsvSkip } from "../_lib/audience-csv";

export interface ImportSummaryProps {
  added: number;
  skipped: CsvSkip[];
}

/** How many rows landed, and every one that did not, by line number. */
export function ImportSummary({ added, skipped }: ImportSummaryProps) {
  const shown = skipped.slice(0, 8);

  return (
    <div className="space-y-3 rounded-lg bg-muted/50 p-3 text-sm">
      <p className="flex items-center gap-2 font-medium">
        {added > 0 ? (
          <CheckCircle2Icon aria-hidden className="size-4 text-success" />
        ) : (
          <AlertTriangleIcon aria-hidden className="size-4 text-warning" />
        )}
        {added === 0
          ? "Nothing to add from this file"
          : `${added} ${added === 1 ? "person" : "people"} ready to add`}
      </p>

      {skipped.length > 0 ? (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">
            {skipped.length} {skipped.length === 1 ? "row" : "rows"} will be skipped
          </p>
          <ul className="space-y-0.5 text-xs text-muted-foreground">
            {shown.map((skip) => (
              <li key={skip.line}>
                Line {skip.line}: {skip.reason}
              </li>
            ))}
            {skipped.length > shown.length ? (
              <li>…and {skipped.length - shown.length} more</li>
            ) : null}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
