"use client";

import { EyeIcon, LoaderCircleIcon, SaveIcon, SendIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import type { CampaignStatus } from "@/types/campaign";

export interface BuilderActionsProps {
  /** `null` while creating - there is nothing published to compare against. */
  status: CampaignStatus | null;
  pending: boolean;
  dirty: boolean;
  previewHref?: string;
  onSaveDraft: () => void;
  onPublish: () => void;
}

/**
 * The builder's two commitments, with two different contracts.
 *
 * Save needs only a name; Publish runs the full contract. Publish is never
 * disabled - it reports every unmet requirement when pressed, because a
 * greyed-out button that will not say what is wrong is the worse failure. On
 * an already-published campaign there is nothing to publish, so the pair
 * collapses to a single Save that says where the change lands.
 */
export function BuilderActions({
  status,
  pending,
  dirty,
  previewHref,
  onSaveDraft,
  onPublish,
}: BuilderActionsProps) {
  const isDraft = status === null || status === "DRAFT";
  const spinner = <LoaderCircleIcon data-icon="inline-start" className="animate-spin" />;

  return (
    <div className="sticky bottom-0 z-20 -mx-5 mt-2 border-t bg-background/90 px-5 py-3 backdrop-blur">
      <div className="flex flex-wrap items-center gap-2">
        {previewHref ? (
          <Button asChild variant="ghost" size="lg">
            <Link href={previewHref}>
              <EyeIcon data-icon="inline-start" />
              Preview
            </Link>
          </Button>
        ) : null}

        <p className="mr-auto text-sm text-muted-foreground" aria-live="polite">
          {pending
            ? "Saving…"
            : dirty
              ? "Unsaved changes"
              : isDraft
                ? "Draft"
                : "Live changes apply immediately"}
        </p>

        <Button
          type="button"
          variant={isDraft ? "outline" : "default"}
          size="lg"
          disabled={pending}
          onClick={onSaveDraft}
        >
          {pending ? spinner : <SaveIcon data-icon="inline-start" />}
          {isDraft ? "Save as draft" : "Save changes"}
        </Button>

        {isDraft ? (
          <Button type="button" size="lg" disabled={pending} onClick={onPublish}>
            {pending ? spinner : <SendIcon data-icon="inline-start" />}
            Publish
          </Button>
        ) : null}
      </div>
    </div>
  );
}
