import { listAudiences } from "@/lib/api/audiences";

import { PageHeader } from "../_components/page-header";
import { PageShell } from "../_components/page-shell";
import { AudienceCreateDialog } from "./_components/audience-create-dialog";
import { AudienceEmptyState } from "./_components/audience-empty-state";
import { AudienceList } from "./_components/audience-list";

export const metadata = {
  title: "Audiences",
  description: "The lists your campaigns are sent to.",
};

export default async function AudiencesPage({ searchParams }: PageProps<"/audiences">) {
  const { q } = await searchParams;
  const search = typeof q === "string" ? q : undefined;
  const { items, total } = await listAudiences({ search, limit: 50 });

  return (
    <PageShell className="space-y-8">
      <PageHeader
        eyebrow="Audiences"
        title="Who your campaigns reach"
        description="A list of people, built once and reusable by every campaign. A single customer is a list of one."
        actions={<AudienceCreateDialog />}
      />

      {items.length === 0 ? (
        <AudienceEmptyState searching={Boolean(search)} />
      ) : (
        <AudienceList audiences={items} total={total} />
      )}
    </PageShell>
  );
}
