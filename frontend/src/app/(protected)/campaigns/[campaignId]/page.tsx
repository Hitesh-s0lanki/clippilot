import { redirect } from "next/navigation";

/**
 * A bare campaign URL has no view of its own.
 *
 * It resolves to the builder, which is where a campaign is worked on and the
 * only view that is useful at every status - analytics on a draft is an empty
 * screen by definition.
 */
export default async function CampaignIndexPage({ params }: PageProps<"/campaigns/[campaignId]">) {
  const { campaignId } = await params;
  redirect(`/campaigns/${campaignId}/edit`);
}
