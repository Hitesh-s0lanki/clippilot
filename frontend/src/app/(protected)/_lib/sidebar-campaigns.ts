import "server-only";

import { cache } from "react";

import { listCampaigns } from "@/lib/api/campaigns";
import type { CampaignSummary } from "@/types/campaign";

/** How many campaigns the rail lists before deferring to the dashboard. */
export const SIDEBAR_CAMPAIGN_LIMIT = 5;

export interface SidebarCampaigns {
  /** The most recently created campaigns, newest first. */
  recent: CampaignSummary[];
  /** Every campaign the owner has, so the rail can say what it is not showing. */
  total: number;
  /** `true` when the list could not be loaded, so the rail can say so quietly. */
  failed: boolean;
}

const EMPTY: SidebarCampaigns = { recent: [], total: 0, failed: true };

/**
 * What the sidebar needs to know about the owner's campaigns.
 *
 * `cache` collapses this to one round trip however many parts of the rail ask
 * for it during a render - the campaigns branch and the customers link both do.
 *
 * A failure resolves to an empty result instead of throwing. This is chrome: if
 * the API is down the dashboard's own error boundary should say so on the
 * screen, not take the navigation down with it and strand the user on a blank
 * shell with no way out.
 */
export const loadSidebarCampaigns = cache(async (): Promise<SidebarCampaigns> => {
  try {
    const recent = await listCampaigns({
      limit: SIDEBAR_CAMPAIGN_LIMIT,
      includeArchived: false,
    });

    return { recent: recent.items, total: recent.total, failed: false };
  } catch {
    return EMPTY;
  }
});
