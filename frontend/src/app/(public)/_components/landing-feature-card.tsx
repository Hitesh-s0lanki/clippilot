import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export interface LandingFeatureCardProps {
  title: string;
  description: string;
  /** Real enum members, limits and extensions, rendered as chips. */
  facts: ReadonlyArray<string>;
  Icon: LucideIcon;
  /** Leads a row of the bento grid, so it takes two of the three columns. */
  wide: boolean;
}

/**
 * One capability, stated rather than described.
 *
 * The card carries a single line of prose and then the actual values - the
 * four special categories, the three video extensions, the three intents.
 * Naming them is both shorter than explaining them and worth more to a reader
 * deciding whether the product fits: "four special categories" is a claim,
 * "Financial products · Credit · Employment · Housing" is an answer.
 */
export function LandingFeatureCard({
  title,
  description,
  facts,
  Icon,
  wide,
}: LandingFeatureCardProps) {
  return (
    <li className={cn(wide && "sm:col-span-2")}>
      <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-6">
        <span className="grid size-10 place-items-center rounded-xl bg-primary/10">
          <Icon aria-hidden className="size-5 text-primary" />
        </span>
        <h3 className="mt-4 font-heading font-semibold tracking-tight text-balance">{title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-pretty text-muted-foreground">
          {description}
        </p>
        <ul className="mt-auto flex flex-wrap gap-1.5 pt-4">
          {facts.map((fact) => (
            <li
              key={fact}
              className="rounded-md bg-muted px-2 py-1 font-mono text-xs text-muted-foreground"
            >
              {fact}
            </li>
          ))}
        </ul>
      </article>
    </li>
  );
}
