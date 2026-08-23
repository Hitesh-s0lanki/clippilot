import { ArrowRightIcon, CircleCheckIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { FollowUp } from "@/types/preview";

export interface PreviewFollowUpProps {
  followUp: FollowUp;
  /** The label of the option that was chosen, echoed back as confirmation. */
  chosenLabel: string;
}

/**
 * What the recipient sees after answering.
 *
 * A link follow-up is offered as a button rather than an automatic redirect:
 * being thrown to another site the instant you click is disorienting, and it
 * takes the confirmation away before it can be read. The destination is shown
 * so nobody has to guess where the button goes.
 */
export function PreviewFollowUp({ followUp, chosenLabel }: PreviewFollowUpProps) {
  return (
    <div className="space-y-3 rounded-xl border border-success/30 bg-success/5 p-5 text-center">
      <p className="flex items-center justify-center gap-1.5 text-sm font-medium text-success">
        <CircleCheckIcon aria-hidden className="size-4" />
        You chose “{chosenLabel}”
      </p>

      {followUp.follow_up_type === "URL" && followUp.follow_up_url ? (
        <>
          <p className="leading-relaxed text-pretty">One more step - your next page is ready.</p>
          <Button asChild size="lg" className="min-h-11 px-5 text-base">
            <a href={followUp.follow_up_url} rel="noreferrer noopener">
              Continue
              <ArrowRightIcon data-icon="inline-end" />
            </a>
          </Button>
          <p className="truncate font-mono text-xs text-muted-foreground">
            {followUp.follow_up_url}
          </p>
        </>
      ) : (
        <p className="text-base leading-relaxed text-pretty">
          {followUp.follow_up_message ?? "Thanks - your response has been recorded."}
        </p>
      )}
    </div>
  );
}
