import { ShieldCheckIcon, SparklesIcon } from "lucide-react";

import { marketing } from "@/config/marketing";

import { LandingBackdrop } from "./landing-backdrop";
import { LandingHeroActions } from "./landing-hero-actions";
import { LandingHeroVisual } from "./landing-hero-visual";

/**
 * The landing hero: the promise, the two buttons, and the product beside them.
 *
 * The only band on the page that runs edge to edge, which is why it brings its
 * own centred container rather than sitting inside the page's - the colour
 * wash behind it has to reach the window, not stop at a 64rem rectangle.
 *
 * The headline is split in two in `marketing.hero` so the second clause can
 * carry the brand colour without the copy being cut up in the markup.
 */
export function LandingHero() {
  const { eyebrow, title, titleAccent, description, note } = marketing.hero;

  return (
    <section className="relative isolate">
      <LandingBackdrop />

      <div className="mx-auto grid w-full max-w-5xl items-center gap-12 px-5 py-14 sm:py-20 lg:grid-cols-[minmax(0,1fr)_minmax(0,23rem)] lg:gap-12">
        <div>
          <p className="inline-flex items-center gap-2 rounded-4xl border border-border bg-card/70 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur">
            <SparklesIcon aria-hidden className="size-3.5 text-primary" />
            {eyebrow}
          </p>

          <h1 className="mt-5 font-heading text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
            {title} <span className="text-primary">{titleAccent}</span>
          </h1>

          <p className="mt-5 max-w-xl text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">
            {description}
          </p>

          <LandingHeroActions />

          <p className="mt-6 flex max-w-md items-start gap-2 text-sm text-muted-foreground">
            <ShieldCheckIcon aria-hidden className="mt-0.5 size-4 shrink-0 text-success" />
            {note}
          </p>
        </div>

        <LandingHeroVisual />
      </div>
    </section>
  );
}
