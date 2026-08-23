import type { Metadata } from "next";

import { listPublicCampaigns } from "@/lib/api";

import { AdsEmptyState } from "./_components/ads-empty-state";
import { AdsGrid } from "./_components/ads-grid";
import { AdsHeader } from "./_components/ads-header";
import { AdsPagination } from "./_components/ads-pagination";
import { PAGE_SIZE, parseAdsQuery } from "./_lib/ads-query";

export const metadata: Metadata = {
  title: "Ads library",
  description: "Every interactive video campaign that is live on ClipPilot right now.",
};

export default async function AdsPage({ searchParams }: PageProps<"/ads">) {
  const query = parseAdsQuery(await searchParams);
  const library = await listPublicCampaigns({ limit: PAGE_SIZE, offset: query.offset });

  return (
    <main className="mx-auto w-full max-w-5xl flex-1 space-y-8 px-5 py-12 sm:py-16">
      <AdsHeader total={library.total} />

      {library.items.length === 0 ? <AdsEmptyState /> : <AdsGrid ads={library.items} />}

      <AdsPagination query={query} total={library.total} shown={library.items.length} />
    </main>
  );
}
