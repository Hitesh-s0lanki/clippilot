"use client";

import { Trash2Icon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { toast } from "sonner";

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
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { deleteAudienceAction } from "@/lib/actions/audience-actions";
import { formatCount } from "@/lib/format";
import type { Audience } from "@/types/audience";

export interface AudienceDeleteButtonProps {
  audience: Audience;
}

/**
 * Deletes the whole list.
 *
 * Disabled while any campaign still targets it. The API refuses that case with
 * a 409 anyway; saying so on the button means the user learns it before they
 * commit rather than after, and the tooltip names the reason.
 */
export function AudienceDeleteButton({ audience }: AudienceDeleteButtonProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const inUse = audience.campaign_count > 0;

  function confirm() {
    startTransition(async () => {
      const result = await deleteAudienceAction(audience.id);

      if (!result.ok) {
        toast.error(result.message);
        return;
      }

      toast.success(`“${audience.name}” deleted`);
      router.push("/audiences");
    });
  }

  if (inUse) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          {/* A span, because a disabled button does not fire the events a
              tooltip listens for - and the reason is the whole point here. */}
          <span tabIndex={0}>
            <Button variant="outline" disabled aria-label="Delete audience">
              <Trash2Icon aria-hidden />
            </Button>
          </span>
        </TooltipTrigger>
        <TooltipContent>
          {formatCount(audience.campaign_count)} campaign
          {audience.campaign_count === 1 ? "" : "s"} still target this list
        </TooltipContent>
      </Tooltip>
    );
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" aria-label="Delete audience">
          <Trash2Icon aria-hidden />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete “{audience.name}”?</AlertDialogTitle>
          <AlertDialogDescription>
            This permanently deletes the list and all {formatCount(audience.member_count)} people in
            it. Campaign analytics are unaffected.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Keep audience</AlertDialogCancel>
          <AlertDialogAction disabled={pending} onClick={confirm}>
            {pending ? "Deleting…" : "Delete permanently"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
