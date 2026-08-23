import { cn } from "@/lib/utils";

/** A campaign's two options, as they are counted back. Illustrative figures. */
const OPTIONS = [
  {
    label: "Tell me more",
    intent: "Positive",
    clicks: 39,
    share: "62%",
    width: "w-[62%]",
    tone: "bg-chart-1",
  },
  {
    label: "Not interested",
    intent: "Negative",
    clicks: 24,
    share: "38%",
    width: "w-[38%]",
    tone: "bg-chart-2",
  },
] as const;

const METRICS = [
  { label: "Views", value: "148" },
  { label: "Interactions", value: "63" },
  { label: "Interaction rate", value: "42.6%" },
] as const;

export function LandingResponseCard() {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center gap-2">
        <h3 className="font-heading font-semibold tracking-tight">What comes back</h3>
        {/* These figures are invented. Saying so beside them costs one word and
            keeps the card from reading as a real campaign's results. */}
        <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
          Illustrative
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-3 gap-3">
        {METRICS.map(({ label, value }) => (
          <div key={label} className="rounded-xl border border-border p-3">
            <dt className="text-xs text-muted-foreground">{label}</dt>
            <dd className="mt-1 font-heading text-xl font-semibold tracking-tight tabular-nums">
              {value}
            </dd>
          </div>
        ))}
      </dl>

      <span aria-hidden className="mt-6 flex h-2 overflow-hidden rounded-full bg-muted">
        {OPTIONS.map(({ label, width, tone }) => (
          <span key={label} className={cn(width, tone)} />
        ))}
      </span>

      <ul className="mt-4 space-y-3">
        {OPTIONS.map(({ label, intent, clicks, share, tone }) => (
          <li key={label} className="flex items-center gap-3 text-sm">
            <span aria-hidden className={cn("size-2.5 shrink-0 rounded-full", tone)} />
            <span className="font-medium">{label}</span>
            <span className="text-xs text-muted-foreground">{intent}</span>
            <span className="ml-auto text-muted-foreground tabular-nums">
              {clicks} · {share}
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-4 border-t border-border pt-4 text-sm leading-relaxed text-pretty text-muted-foreground">
        Every option gets a row, including one nobody clicked.
      </p>
    </article>
  );
}
