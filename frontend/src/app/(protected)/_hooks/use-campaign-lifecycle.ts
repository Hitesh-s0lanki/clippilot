"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { toast } from "sonner";

import { changeCampaignStatusAction, deleteCampaignAction } from "@/lib/actions/campaign-actions";
import type { CampaignStatus } from "@/types/campaign";

export interface UseCampaignLifecycleOptions {
  campaignId: string;
  campaignName: string;
  /** Where to go after a delete. Stay put when the row simply disappears. */
  redirectAfterDelete?: string;
}

export interface CampaignLifecycle {
  pending: boolean;
  setStatus: (status: CampaignStatus) => void;
  remove: () => void;
}

const SUCCESS_MESSAGE: Record<CampaignStatus, string> = {
  ACTIVE: "Campaign is live.",
  PAUSED: "Campaign paused. Recipients can no longer open it.",
  DRAFT: "Campaign returned to draft.",
  SCHEDULED: "Campaign scheduled.",
  COMPLETED: "Campaign marked as completed.",
  ARCHIVED: "Campaign archived.",
};

/**
 * Lifecycle transitions from anywhere a campaign is shown.
 *
 * Every call is a Server Action, so the server stays the authority on which
 * transitions are legal - this hook never pre-decides that a move will work,
 * it renders what came back. A rejection is surfaced as its own message
 * ("recorded activity, can no longer be returned to draft") rather than a
 * generic failure, because that message is the entire explanation.
 */
export function useCampaignLifecycle({
  campaignId,
  campaignName,
  redirectAfterDelete,
}: UseCampaignLifecycleOptions): CampaignLifecycle {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function setStatus(status: CampaignStatus) {
    startTransition(async () => {
      const result = await changeCampaignStatusAction(campaignId, status);

      if (!result.ok) {
        toast.error(result.message);
        return;
      }

      toast.success(SUCCESS_MESSAGE[result.data.status] ?? SUCCESS_MESSAGE[status]);
      router.refresh();
    });
  }

  function remove() {
    startTransition(async () => {
      const result = await deleteCampaignAction(campaignId);

      if (!result.ok) {
        toast.error(result.message);
        return;
      }

      toast.success(`"${campaignName}" was deleted.`);
      if (redirectAfterDelete) {
        router.push(redirectAfterDelete);
      }
      router.refresh();
    });
  }

  return { pending, setStatus, remove };
}
