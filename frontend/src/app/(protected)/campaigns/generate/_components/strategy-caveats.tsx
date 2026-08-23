import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CircleAlertIcon, InfoIcon } from "lucide-react";

import type { AgentRunMeta, CampaignStrategy } from "@/types/agent";

export interface StrategyCaveatsProps {
  strategy: CampaignStrategy;
  meta: AgentRunMeta;
}

/**
 * What the agent could not settle, and what it could not reach.
 *
 * Shown above the draft rather than buried under it. A generated campaign is
 * only trustworthy to the extent its gaps are visible, and "Firecrawl was
 * unreachable so this is guesswork" changes what the draft is worth.
 */
export function StrategyCaveats({ strategy, meta }: StrategyCaveatsProps) {
  const hasNotes = meta.degraded && meta.notes.length > 0;
  const hasQuestions = strategy.open_questions.length > 0;

  if (!hasNotes && !hasQuestions) return null;

  return (
    <div className="space-y-3">
      {hasNotes ? (
        <Alert>
          <CircleAlertIcon className="text-warning" />
          <AlertTitle>Worked with less than it asked for</AlertTitle>
          <AlertDescription>
            <ul className="space-y-1">
              {meta.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      ) : null}

      {hasQuestions ? (
        <Alert>
          <InfoIcon />
          <AlertTitle>Still yours to decide</AlertTitle>
          <AlertDescription>
            <ul className="space-y-1">
              {strategy.open_questions.map((question) => (
                <li key={question}>{question}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
