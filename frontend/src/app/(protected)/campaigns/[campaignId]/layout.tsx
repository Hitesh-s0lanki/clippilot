import { PageShell } from "../../_components/page-shell";
import { loadCampaign } from "../_lib/load-campaign";
import { CampaignHeader } from "./_components/campaign-header";
import { CampaignTabs } from "./_components/campaign-tabs";

/**
 * The shell shared by a campaign's views.
 *
 * The campaign is fetched here for the header and again by each page for its
 * own content - `getCampaign` is wrapped in React's `cache`, so both resolve
 * from one request rather than two.
 *
 * From `md` up the console shell is the height of the viewport and its content
 * area is the single scroll container, so the header and the tabs are pinned to
 * the top of it and switching tabs never means scrolling back up to find them.
 * A form below them sticks its actions to the bottom of the same container -
 * to the bottom of the screen, rather than to the end of a document that keeps
 * growing.
 */
export default async function CampaignLayout({
  children,
  params,
}: LayoutProps<"/campaigns/[campaignId]">) {
  const { campaignId } = await params;
  const campaign = await loadCampaign(campaignId);

  return (
    <PageShell className="flex flex-col gap-6">
      {/* Pinned to the top of the scrolling pane. The negative gutters match
          PageShell's exactly, so the backdrop reaches the edges without
          widening the container and introducing a sideways scrollbar; the
          padding replaces the shell's own, which the offset cancels.

          `top-14` below md, `top-0` from md up: on a phone the page scrolls as
          a document and the topbar is sticky over it, so sticking at 0 would
          park this underneath it. From md the scroll container already starts
          below the topbar, so 0 is its top. */}
      <div className="sticky top-14 z-20 -mx-4 -mt-8 flex flex-col gap-4 bg-background/95 px-4 pt-8 pb-3 backdrop-blur sm:-mx-6 sm:px-6 md:top-0 lg:-mt-10 lg:pt-10">
        <CampaignHeader campaign={campaign} />
        <CampaignTabs campaignId={campaign.id} />
      </div>
      {children}
    </PageShell>
  );
}
