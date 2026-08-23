import { LandingCapabilities } from "./_components/landing-capabilities";
import { LandingCta } from "./_components/landing-cta";
import { LandingFaq } from "./_components/landing-faq";
import { LandingFeatures } from "./_components/landing-features";
import { LandingFlow } from "./_components/landing-flow";
import { LandingHero } from "./_components/landing-hero";
import { LandingShowcase } from "./_components/landing-showcase";
import { PublicChrome } from "./_components/public-chrome";

export default function HomePage() {
  return (
    <PublicChrome>
      {/* The hero runs edge to edge and centres its own content; every section
          below it shares the one container. */}
      <main className="flex-1">
        <LandingHero />

        <div className="mx-auto w-full max-w-5xl px-5 pb-14 sm:pb-20">
          <LandingCapabilities />
          <LandingFlow />
          <LandingFeatures />
          <LandingShowcase />
          <LandingFaq />
          <LandingCta />
        </div>
      </main>
    </PublicChrome>
  );
}
