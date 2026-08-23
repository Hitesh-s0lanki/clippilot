"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";

export interface AdFormActionsProps {
  campaignId: string;
  /** Present when editing, so the ad can be previewed as it stands. */
  adId?: string;
  pending: boolean;
  dirty: boolean;
  onSave: () => void;
}

/**
 * Save and cancel, pinned to the bottom of the viewport.
 *
 * Sticky rather than at the end of the document: a form you have to scroll to
 * the bottom of to save is a form people abandon halfway, and the button that
 * commits the work should never be the thing that is off screen.
 */
export function AdFormActions({ campaignId, adId, pending, dirty, onSave }: AdFormActionsProps) {
  return (
    <div className="sticky bottom-0 z-20 border-t border-border bg-background/95 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="flex flex-wrap items-center justify-end gap-2">
        {dirty ? <p className="mr-auto text-xs text-muted-foreground">Unsaved changes</p> : null}

        {adId ? (
          <Button asChild variant="ghost" size="sm">
            <Link href={`/campaigns/${campaignId}/preview?ad_id=${adId}`}>Preview</Link>
          </Button>
        ) : null}

        <Button asChild variant="outline" size="sm">
          <Link href={`/campaigns/${campaignId}/ads`}>Cancel</Link>
        </Button>

        <Button type="button" size="sm" disabled={pending} onClick={onSave}>
          {pending ? "Saving…" : adId ? "Save ad" : "Add ad"}
        </Button>
      </div>
    </div>
  );
}
