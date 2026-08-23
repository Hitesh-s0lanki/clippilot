"use client";

import {
  ArchiveIcon,
  BarChart3Icon,
  MoreHorizontalIcon,
  PauseIcon,
  PlayIcon,
  RotateCcwIcon,
  Trash2Icon,
} from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { lifecycleActions } from "@/lib/campaign-status";
import type { CampaignStatus } from "@/types/campaign";

import { useCampaignLifecycle } from "../_hooks/use-campaign-lifecycle";
import { CampaignDeleteDialog } from "./campaign-delete-dialog";

export interface CampaignActionsMenuProps {
  campaignId: string;
  campaignName: string;
  status: CampaignStatus;
  /** Views plus interactions, used to warn before a destructive delete. */
  eventCount: number;
  /** Set on the campaign's own screens, where the row cannot just vanish. */
  redirectAfterDelete?: string;
}

/**
 * The overflow menu on a campaign card and in the campaign header.
 *
 * It offers only the transitions the lifecycle allows from the current status,
 * so the menu never shows "Resume" on a draft. The server re-checks anyway -
 * this is about not offering a dead end, not about trusting the client.
 */
export function CampaignActionsMenu({
  campaignId,
  campaignName,
  status,
  eventCount,
  redirectAfterDelete,
}: CampaignActionsMenuProps) {
  const { pending, setStatus, remove } = useCampaignLifecycle({
    campaignId,
    campaignName,
    redirectAfterDelete,
  });
  const actions = lifecycleActions(status);
  const hasTransitions =
    actions.canPublish || actions.canResume || actions.canPause || actions.canUnpublish;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          disabled={pending}
          aria-label={`More actions for ${campaignName}`}
        >
          <MoreHorizontalIcon />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem asChild>
          <Link href={`/campaigns/${campaignId}/analytics`}>
            <BarChart3Icon />
            View analytics
          </Link>
        </DropdownMenuItem>

        {hasTransitions ? <DropdownMenuSeparator /> : null}

        {actions.canPublish ? (
          <DropdownMenuItem onSelect={() => setStatus("ACTIVE")}>
            <PlayIcon />
            Publish
          </DropdownMenuItem>
        ) : null}

        {actions.canResume ? (
          <DropdownMenuItem onSelect={() => setStatus("ACTIVE")}>
            <PlayIcon />
            Resume
          </DropdownMenuItem>
        ) : null}

        {actions.canPause ? (
          <DropdownMenuItem onSelect={() => setStatus("PAUSED")}>
            <PauseIcon />
            Pause
          </DropdownMenuItem>
        ) : null}

        {actions.canUnpublish ? (
          <DropdownMenuItem onSelect={() => setStatus("DRAFT")}>
            <RotateCcwIcon />
            Return to draft
          </DropdownMenuItem>
        ) : null}

        <DropdownMenuSeparator />

        {actions.canArchive ? (
          <DropdownMenuItem onSelect={() => setStatus("ARCHIVED")}>
            <ArchiveIcon />
            Archive
          </DropdownMenuItem>
        ) : null}

        <CampaignDeleteDialog
          campaignName={campaignName}
          eventCount={eventCount}
          pending={pending}
          onConfirm={remove}
        >
          <DropdownMenuItem variant="destructive" onSelect={(event) => event.preventDefault()}>
            <Trash2Icon />
            Delete
          </DropdownMenuItem>
        </CampaignDeleteDialog>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
