import { Badge } from "@/components/ui/badge";
import type { CampaignStrategy } from "@/types/agent";

export interface StrategyAnalysisProps {
  strategy: CampaignStrategy;
}

/**
 * What the agent found, and what it recommends because of it.
 *
 * The competitor gap is the load-bearing part: the angle is only interesting
 * next to what everyone else is already saying, so the two sit together rather
 * than in separate cards.
 */
export function StrategyAnalysis({ strategy }: StrategyAnalysisProps) {
  const { business, competitors, creative } = strategy;

  return (
    <div className="space-y-4">
      <section className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="font-heading font-semibold tracking-tight">
            {business.name ?? "The business"}
          </h2>
          {business.industry ? <Badge variant="secondary">{business.industry}</Badge> : null}
          {strategy.researched ? null : <Badge variant="warning">No research</Badge>}
        </div>
        <p className="mt-2 text-sm text-pretty text-muted-foreground">{business.summary}</p>

        {business.value_propositions.length > 0 ? (
          <ul className="mt-3 flex flex-wrap gap-1.5">
            {business.value_propositions.map((claim) => (
              <li
                key={claim}
                className="rounded-4xl border border-border px-2.5 py-1 text-xs text-muted-foreground"
              >
                {claim}
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      {competitors.length > 0 ? (
        <section className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
          <h2 className="font-heading font-semibold tracking-tight">
            What {competitors.length === 1 ? "the competitor is" : "competitors are"} saying
          </h2>
          <ul className="mt-3 space-y-4">
            {competitors.map((competitor) => (
              <li key={competitor.name} className="border-l-2 border-border pl-3">
                <p className="text-sm font-medium">{competitor.name}</p>
                {competitor.positioning ? (
                  <p className="text-sm text-muted-foreground">{competitor.positioning}</p>
                ) : null}
                {competitor.hooks.length > 0 ? (
                  <p className="mt-1 text-sm text-pretty text-muted-foreground italic">
                    “{competitor.hooks[0]}”
                  </p>
                ) : null}
                {competitor.gap ? (
                  <p className="mt-1 text-sm text-pretty">
                    <span className="text-muted-foreground">Gap: </span>
                    {competitor.gap}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
        <h2 className="font-heading font-semibold tracking-tight">The angle</h2>
        <p className="mt-2 text-sm text-pretty">{creative.angle}</p>
        <p className="mt-2 text-sm text-pretty text-muted-foreground">{creative.why_it_wins}</p>

        <h3 className="mt-4 text-sm font-medium">The video to record</h3>
        <p className="mt-1 text-sm text-pretty text-muted-foreground">{creative.video_concept}</p>

        {creative.avoid.length > 0 ? (
          <p className="mt-3 text-sm text-pretty text-muted-foreground">
            <span className="font-medium text-foreground">Avoid: </span>
            {creative.avoid.join(" · ")}
          </p>
        ) : null}
      </section>
    </div>
  );
}
