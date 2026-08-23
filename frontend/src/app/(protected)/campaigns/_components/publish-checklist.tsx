import { CircleCheckIcon, CircleDashedIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { CampaignEffectiveStatus } from "@/types/campaign";

import { describeField } from "../_lib/campaign-form-sections";
import { fieldId } from "../_lib/field-id";

export interface PublishChecklistProps {
  /** `publish_blockers` from the API - field paths, computed on every read. */
  blockers: string[];
  status: CampaignEffectiveStatus;
}

/**
 * What still stands between this draft and publishing.
 *
 * The API returns the blockers on every read rather than only when a publish
 * is attempted, so the answer is on screen before the button is pressed - the
 * builder never has to guess, and nobody has to press Publish to find out what
 * is missing. Once the list is empty the card says so instead of disappearing:
 * "ready" is information too.
 */
export function PublishChecklist({ blockers, status }: PublishChecklistProps) {
  if (status !== "DRAFT" && status !== "INCOMPLETE") return null;

  if (blockers.length === 0) {
    return (
      <Alert>
        <CircleCheckIcon className="text-success" />
        <AlertTitle>Ready to publish</AlertTitle>
        <AlertDescription>
          Everything the publish contract needs is filled in. Publishing makes this openable by its
          recipients straight away.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Alert>
      <CircleDashedIcon className="text-warning" />
      <AlertTitle>
        {blockers.length} {blockers.length === 1 ? "item" : "items"} left before this can be
        published
      </AlertTitle>
      <AlertDescription>
        <ul className="flex flex-wrap gap-x-2 gap-y-1">
          {blockers.map((blocker) => (
            <li key={blocker}>
              <a
                href={`#${fieldId(blocker)}`}
                className="rounded underline underline-offset-2 hover:no-underline focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                {describeField(blocker)}
              </a>
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
