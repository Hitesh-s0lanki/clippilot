import { marketing } from "@/config/marketing";

import { LandingFeatureCard } from "./landing-feature-card";
import { LandingSection } from "./landing-section";

/**
 * The capability grid.
 *
 * A bento rather than an even grid: the three cards that carry the product's
 * argument - personalisation, compliance, analytics - are twice as wide, so
 * the eye picks them up first. Three columns and three double-width cards tile
 * exactly, which is why the order in `marketing.features` is not alphabetical.
 */
export function LandingFeatures() {
  return (
    <LandingSection
      id="features"
      eyebrow="What you configure"
      title="Everything a real campaign needs, in one form."
      description="The fields a regulated campaign is reviewed against - and it will not publish until they hold together."
    >
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {marketing.features.map((feature) => (
          <LandingFeatureCard
            key={feature.id}
            title={feature.title}
            description={feature.description}
            facts={feature.facts}
            Icon={feature.Icon}
            wide={feature.wide}
          />
        ))}
      </ul>
    </LandingSection>
  );
}
