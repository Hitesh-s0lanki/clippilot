import { LandingCapabilities } from "./_components/landing-capabilities";
import { LandingCta } from "./_components/landing-cta";
import { LandingFaq } from "./_components/landing-faq";
import { LandingFeatures } from "./_components/landing-features";
import { LandingFlow } from "./_components/landing-flow";
import { LandingHero } from "./_components/landing-hero";
import { LandingShowcase } from "./_components/landing-showcase";

export default function HomePage() {
  return (
    // The hero runs edge to edge and centres its own content; every section
    // below it shares the one container. The negative margin is the height of
    // the floating header, so the hero's colour wash reaches the top of the
    // window and the bar floats on top of it rather than above it.
    <main className="-mt-17 flex-1">
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
  );
}
