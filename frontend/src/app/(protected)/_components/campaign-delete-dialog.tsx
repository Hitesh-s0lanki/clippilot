"use client";

import type { ReactNode } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export interface CampaignDeleteDialogProps {
  campaignName: string;
  /** Recorded views and interactions, so the warning can be specific. */
  eventCount: number;
  pending: boolean;
  onConfirm: () => void;
  children: ReactNode;
}

/**
 * Confirmation for the one action that cannot be undone.
 *
 * Deleting a campaign takes its events with it, so the dialog names the
 * campaign and says how much history goes with it rather than asking a generic
 * "are you sure?" - archiving is offered as the reversible alternative.
 */
export function CampaignDeleteDialog({
  campaignName,
  eventCount,
  pending,
  onConfirm,
  children,
}: CampaignDeleteDialogProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete “{campaignName}”?</AlertDialogTitle>
          <AlertDialogDescription>
            {eventCount > 0
              ? `This permanently deletes the campaign and all ${eventCount} recorded events. Archive it instead to keep the analytics.`
              : "This permanently deletes the campaign. Archive it instead if you may want it back."}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Keep campaign</AlertDialogCancel>
          <AlertDialogAction disabled={pending} onClick={onConfirm}>
            {pending ? "Deleting…" : "Delete permanently"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
