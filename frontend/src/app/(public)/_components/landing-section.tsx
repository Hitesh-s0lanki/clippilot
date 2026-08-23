import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface LandingSectionProps {
  /** Doubles as the anchor the header and footer links point at. */
  id: string;
  eyebrow: string;
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

/**
 * One band of the landing page: a rule, an eyebrow, a heading, and the block.
 *
 * Every section on the page is built from this so the rhythm - spacing, type
 * scale, where the eye lands first - is identical down the whole page rather
 * than re-decided per section. `scroll-mt` clears the sticky header, so an
 * anchor link does not park the heading underneath it.
 */
export function LandingSection({
  id,
  eyebrow,
  title,
  description,
  children,
  className,
}: LandingSectionProps) {
  const headingId = `${id}-heading`;

  return (
    <section
      id={id}
      aria-labelledby={headingId}
      className={cn("scroll-mt-24 border-t border-border pt-12 sm:pt-20", className)}
    >
      <p className="text-sm font-medium text-primary">{eyebrow}</p>
      <h2
        id={headingId}
        className="mt-2 max-w-2xl font-heading text-2xl font-semibold tracking-tight text-balance sm:text-3xl"
      >
        {title}
      </h2>
      {description ? (
        <p className="mt-3 max-w-2xl leading-relaxed text-pretty text-muted-foreground">
          {description}
        </p>
      ) : null}
      <div className="mt-8 sm:mt-10">{children}</div>
    </section>
  );
}
