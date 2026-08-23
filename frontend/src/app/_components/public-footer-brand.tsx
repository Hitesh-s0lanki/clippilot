import Link from "next/link";
import { Suspense } from "react";

import { ApiStatusPill, ApiStatusPillSkeleton } from "@/components/api-status-pill";
import { AppLogo } from "@/components/layout/app-logo";
import { siteConfig } from "@/config/site";

/**
 * The footer's identity column: the mark, the promise, and whether the API
 * behind all of it is answering.
 *
 * The probe is wrapped in `<Suspense>` so a slow or dead backend streams in
 * late instead of holding up the whole page - the rest of the footer is static
 * and has no reason to wait for it.
 */
export function PublicFooterBrand() {
  return (
    <div className="max-w-sm">
      <Link
        href="/"
        className="inline-flex items-center gap-2 rounded-lg focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
      >
        <AppLogo size={28} />
        <span className="font-heading font-semibold tracking-tight">{siteConfig.name}</span>
      </Link>

      <p className="mt-3 text-sm leading-relaxed text-pretty text-muted-foreground">
        {siteConfig.description}
      </p>

      <div className="mt-4">
        <Suspense fallback={<ApiStatusPillSkeleton />}>
          <ApiStatusPill />
        </Suspense>
      </div>
    </div>
  );
}
