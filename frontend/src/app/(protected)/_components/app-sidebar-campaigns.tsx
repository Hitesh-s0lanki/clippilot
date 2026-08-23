import { loadSidebarCampaigns } from "../_lib/sidebar-campaigns";
import { AppSidebarCampaignMenu } from "./app-sidebar-campaign-menu";

/**
 * Loads the campaigns the rail lists.
 *
 * Split from the menu so the fetch sits on the server and only plain campaign
 * data crosses into the Client Component that needs the current path. It is
 * rendered inside a `Suspense` boundary, so the rest of the rail - brand, nav,
 * account - paints immediately and this branch streams in behind it.
 */
export async function AppSidebarCampaigns() {
  const { recent, total } = await loadSidebarCampaigns();

  return <AppSidebarCampaignMenu campaigns={recent} total={total} />;
}
