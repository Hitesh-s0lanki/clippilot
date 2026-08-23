import { ArrowRightIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";

import { LandingBackdrop } from "./_components/landing-backdrop";
import { NotFoundSuggestions } from "./_components/not-found-suggestions";
import { PublicChrome } from "./_components/public-chrome";

export const metadata: Metadata = {
  title: "Page not found",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <PublicChrome>
      <main className="relative isolate mx-auto flex w-full max-w-5xl flex-1 flex-col items-start justify-center px-5 py-20 sm:py-28">
        <LandingBackdrop />

        <p className="font-mono text-sm font-medium text-primary">404</p>
        <h1 className="mt-3 max-w-2xl font-heading text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
          That page is not here.
        </h1>
        <p className="mt-4 max-w-xl leading-relaxed text-pretty text-muted-foreground">
          The address may be mistyped, or the campaign it pointed at has been deleted or archived. A
          recipient link that has stopped working usually means the campaign was unpublished rather
          than removed - the person who sent it can tell you which.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg" className="h-11 px-5 text-sm">
            <Link href="/">
              Back to the home page
              <ArrowRightIcon data-icon="inline-end" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="h-11 px-5 text-sm">
            <Link href="/dashboard">Go to campaigns</Link>
          </Button>
        </div>

        <NotFoundSuggestions />
      </main>
    </PublicChrome>
  );
}
