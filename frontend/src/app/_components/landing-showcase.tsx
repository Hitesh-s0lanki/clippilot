import { LandingResolutionCard } from "./landing-resolution-card";
import { LandingResponseCard } from "./landing-response-card";
import { LandingSection } from "./landing-section";

/**
 * The two halves of the product's argument, side by side: what personalisation
 * does to the message going out, and what the response looks like coming back.
 *
 * They share a section because they are the same campaign seen from both ends -
 * splitting them into two bands would lose that.
 */
export function LandingShowcase() {
  return (
    <LandingSection
      id="personalisation"
      eyebrow="Personalisation and analytics"
      title="Written once. Answered once. Counted once."
      description="The message is addressed to a person, the reply is stored against that person, and the numbers on the analytics screen are the same events, added up."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <LandingResolutionCard />
        <LandingResponseCard />
      </div>
    </LandingSection>
  );
}
