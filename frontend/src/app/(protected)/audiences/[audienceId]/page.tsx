import { notFound } from "next/navigation";

import { getAudience, listMembers } from "@/lib/api/audiences";
import { isApiError } from "@/lib/api/errors";

import { PageShell } from "../../_components/page-shell";
import { AudienceDetailHeader } from "./_components/audience-detail-header";
import { AudienceSegmentsPanel } from "./_components/audience-segments-panel";
import { MemberFilters } from "./_components/member-filters";
import { MemberPanel } from "./_components/member-panel";
import { isFiltered, parseMemberQuery, toQueryString } from "./_lib/member-query";

export default async function AudienceDetailPage({
  params,
  searchParams,
}: PageProps<"/audiences/[audienceId]">) {
  const { audienceId } = await params;
  const raw = await searchParams;
  const query = parseMemberQuery(raw);
  const queryString = toQueryString(raw);

  const audience = await getAudience(audienceId).catch((error) => {
    if (isApiError(error) && error.status === 404) notFound();
    throw error;
  });

  const members = await listMembers(audienceId, query);
  const filtered = isFiltered(query);

  return (
    <PageShell className="space-y-8">
      <AudienceDetailHeader audience={audience} />

      <AudienceSegmentsPanel
        audienceId={audience.id}
        segments={audience.segments}
        query={queryString}
        active={{
          age: query.ageGroup,
          gender: query.gender,
          city: query.city,
          country: query.country,
        }}
      />

      <section className="space-y-4">
        <MemberFilters
          audienceId={audience.id}
          query={query}
          queryString={queryString}
          matched={members.total}
          filtered={filtered}
        />
        <MemberPanel
          audience={audience}
          members={members}
          query={queryString}
          page={query.page}
          filtered={filtered}
        />
      </section>
    </PageShell>
  );
}
