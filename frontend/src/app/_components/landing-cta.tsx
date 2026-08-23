import { siteConfig } from "@/config/site";

import { LandingHeroActions } from "./landing-hero-actions";

/**
 * The closing band.
 *
 * A tinted card rather than a solid brand panel, so the same two buttons the
 * hero uses keep their contrast and the page ends on one CTA rather than a
 * second visual language.
 */
export function LandingCta() {
  return (
    <section
      aria-labelledby="cta-heading"
      className="relative isolate mt-14 overflow-hidden rounded-3xl border border-border bg-card p-8 sm:mt-20 sm:p-12"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-br from-primary/12 via-transparent to-chart-2/12"
      />

      <h2
        id="cta-heading"
        className="max-w-2xl font-heading text-2xl font-semibold tracking-tight text-balance sm:text-3xl"
      >
        Build the first campaign in the time it takes to write the message.
      </h2>
      <p className="mt-3 max-w-xl leading-relaxed text-pretty text-muted-foreground">
        {siteConfig.description}
      </p>

      <LandingHeroActions />
    </section>
  );
}
