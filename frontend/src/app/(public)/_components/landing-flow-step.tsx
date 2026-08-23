import {
  BarChart3Icon,
  ChevronRightIcon,
  LayoutGridIcon,
  type LucideIcon,
  PlayCircleIcon,
  SlidersHorizontalIcon,
} from "lucide-react";

import { siteConfig } from "@/config/site";

type FlowStep = (typeof siteConfig.flow)[number];

/** Icons live here rather than in config, which stays free of components. */
const ICONS: Record<FlowStep["id"], LucideIcon> = {
  dashboard: LayoutGridIcon,
  builder: SlidersHorizontalIcon,
  preview: PlayCircleIcon,
  analytics: BarChart3Icon,
};

export interface LandingFlowStepProps {
  step: FlowStep;
  /** The chevron between cards has nothing to point at after the last one. */
  isLast: boolean;
}

export function LandingFlowStep({ step, isLast }: LandingFlowStepProps) {
  const Icon = ICONS[step.id];

  return (
    <li className="relative">
      <article className="flex h-full flex-col rounded-2xl border border-border bg-card p-5">
        <div className="flex items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary/10 font-mono text-sm font-semibold text-primary">
            {step.step}
          </span>
          <span className="rounded-4xl border border-border px-2 py-0.5 text-[0.6875rem] font-medium text-muted-foreground">
            {step.surface}
          </span>
          <Icon aria-hidden className="ml-auto size-4 text-muted-foreground" />
        </div>

        <h3 className="mt-4 font-heading font-semibold tracking-tight">{step.title}</h3>
        <p className="mt-1.5 text-sm leading-relaxed text-pretty text-muted-foreground">
          {step.description}
        </p>
      </article>

      {isLast ? null : (
        <ChevronRightIcon
          aria-hidden
          className="absolute top-9 -right-3.5 hidden size-5 text-border lg:block"
        />
      )}
    </li>
  );
}
