"use client";

import { CheckIcon, LinkIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

export interface CopyPreviewLinkProps {
  campaignId: string;
  /** Resolves the link for one recipient, so their name is filled in. */
  recipientId?: string | null;
}

/**
 * Copies the recipient-facing URL.
 *
 * Built in the browser from `location.origin` rather than from an environment
 * variable, so the link works from whichever host the console is being used
 * on. Falls back to showing the URL in a toast where the clipboard API is
 * unavailable - over plain HTTP, or when permission is refused - because a
 * button that silently does nothing is worse than one that asks you to copy
 * manually.
 */
export function CopyPreviewLink({ campaignId, recipientId }: CopyPreviewLinkProps) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    const query = recipientId ? `?recipient_id=${encodeURIComponent(recipientId)}` : "";
    const url = `${window.location.origin}/preview/${campaignId}${query}`;

    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success("Recipient link copied.");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.message("Copy this link", { description: url, duration: 15_000 });
    }
  }

  return (
    <Button type="button" variant="outline" size="lg" onClick={copy}>
      {copied ? <CheckIcon data-icon="inline-start" /> : <LinkIcon data-icon="inline-start" />}
      {copied ? "Copied" : "Copy link"}
    </Button>
  );
}
