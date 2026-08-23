import { Badge } from "@/components/ui/badge";
import { CTA_LABELS } from "@/types/campaign";
import type { CampaignDraft } from "@/types/agent";

export interface StrategyDraftSummaryProps {
  draft: CampaignDraft;
}

/**
 * The campaign that will be created, before it is.
 *
 * Shows the ads as what they are: complete copy with no video, because the
 * agent writes the concept and the user records the film. Saying so here is
 * what stops the ads screen looking broken a moment later.
 */
export function StrategyDraftSummary({ draft }: StrategyDraftSummaryProps) {
  return (
    <section className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
      <h2 className="font-heading font-semibold tracking-tight">The draft</h2>
      <p className="mt-0.5 text-sm text-muted-foreground">
        {draft.name ?? "Untitled"} · {draft.objective ?? "ENGAGEMENT"} ·{" "}
        {draft.ads.length === 1 ? "1 ad" : `${draft.ads.length} ads`}
      </p>

      <ul className="mt-4 space-y-3">
        {draft.ads.map((ad, index) => (
          <li key={`${ad.name}-${index}`} className="rounded-lg border border-border p-4">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium">{ad.name}</p>
              <Badge variant="secondary">{CTA_LABELS[ad.cta]}</Badge>
              <Badge variant="warning">Needs a video</Badge>
            </div>

            {ad.headline ? <p className="mt-2 text-sm font-medium">{ad.headline}</p> : null}
            {ad.personalised_message ? (
              <p className="mt-1 text-sm text-pretty text-muted-foreground">
                {ad.personalised_message}
              </p>
            ) : null}

            <ul className="mt-3 flex flex-wrap gap-1.5">
              {ad.options.map((option) => (
                <li
                  key={option.position}
                  className="rounded-4xl border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground"
                >
                  {option.label}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}
