import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export interface LandingFeatureCardProps {
  title: string;
  description: string;
  Icon: LucideIcon;
  /** Leads a row of the bento grid, so it takes two of the three columns. */
  wide: boolean;
}

export function LandingFeatureCard({ title, description, Icon, wide }: LandingFeatureCardProps) {
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
      </article>
    </li>
  );
}
