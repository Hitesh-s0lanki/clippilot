import { LoaderCircleIcon } from "lucide-react";

/**
 * What the agent is doing, while it does it.
 *
 * A run reads several pages and can take a minute or two, which is long enough
 * that a bare spinner reads as a hang. Naming the steps is the difference
 * between waiting and wondering whether it broke.
 */
export function GeneratePending() {
  const steps = [
    "Reading your website",
    "Finding and reading competitors",
    "Working out what nobody is saying",
    "Drafting the campaign and its ads",
  ];

  return (
    <div className="rounded-xl border border-border bg-card px-6 py-10 text-center">
      <LoaderCircleIcon aria-hidden className="mx-auto size-6 animate-spin text-primary" />
      <h2 className="mt-4 font-heading font-semibold tracking-tight">Researching</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-pretty text-muted-foreground">
        This takes a minute or two. Nothing is saved until you accept the draft.
      </p>

      <ul className="mx-auto mt-5 max-w-xs space-y-1.5 text-left text-sm text-muted-foreground">
        {steps.map((step) => (
          <li key={step} className="flex items-start gap-2">
            <span
              aria-hidden
              className="mt-1.5 size-1.5 shrink-0 rounded-full bg-muted-foreground/50"
            />
            {step}
          </li>
        ))}
      </ul>
    </div>
  );
}
