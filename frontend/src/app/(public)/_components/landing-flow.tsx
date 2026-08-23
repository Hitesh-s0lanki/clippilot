import { siteConfig } from "@/config/site";

import { LandingFlowStep } from "./landing-flow-step";
import { LandingSection } from "./landing-section";

/**
 * The four steps of the product, in order.
 *
 * An ordered list because the order is the point - dashboard, builder,
 * preview, analytics is one loop, not four features - and the chevrons between
 * the cards say so on wide screens, where four columns would otherwise read as
 * a menu of choices.
 */
export function LandingFlow() {
  return (
    <LandingSection id="how-it-works" eyebrow="How it works" title="One loop, start to finish.">
      <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {siteConfig.flow.map((step, index) => (
          <LandingFlowStep
            key={step.id}
            step={step}
            isLast={index === siteConfig.flow.length - 1}
          />
        ))}
      </ol>
    </LandingSection>
  );
}
