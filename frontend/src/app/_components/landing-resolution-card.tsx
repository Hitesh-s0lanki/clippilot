import { ArrowDownIcon } from "lucide-react";

/** Braces in JSX are an expression delimiter, so the template is a string. */
const TEMPLATE = "Hi {{customer_name}}, we have identified an investment opportunity for you.";

export function LandingResolutionCard() {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-6">
      <h3 className="font-heading font-semibold tracking-tight">What you write</h3>
      <p className="mt-3 rounded-xl border border-border bg-muted/50 p-4 font-mono text-sm leading-relaxed break-words">
        {TEMPLATE}
      </p>

      <ArrowDownIcon aria-hidden className="mt-4 size-4 self-center text-muted-foreground" />

      <h3 className="mt-4 font-heading font-semibold tracking-tight">What Rahul opens</h3>
      <p className="mt-3 rounded-xl border border-primary/25 bg-primary/5 p-4 text-sm leading-relaxed">
        Hi <span className="rounded bg-primary/15 px-1 font-medium text-primary">Rahul</span>, we
        have identified an investment opportunity for you.
      </p>

      <p className="mt-4 border-t border-border pt-4 text-sm leading-relaxed text-pretty text-muted-foreground">
        The same substitution runs over the headline and both follow-up messages. A recipient with
        no name on file gets &ldquo;Hi there&rdquo; rather than a blank, so a preview is never
        broken by missing data.
      </p>
    </article>
  );
}
