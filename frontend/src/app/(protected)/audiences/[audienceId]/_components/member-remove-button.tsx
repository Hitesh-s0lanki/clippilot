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
import { removeMemberAction } from "@/lib/actions/audience-actions";

export interface MemberRemoveButtonProps {
  audienceId: string;
  memberId: string;
  fullName: string;
}

/**
 * Takes one person off the list.
 *
 * Confirmed, because it affects every campaign targeting this audience - which
 * is the trade the account-level list makes, and the one thing about it worth
 * saying out loud before the row disappears.
 */
export function MemberRemoveButton({ audienceId, memberId, fullName }: MemberRemoveButtonProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function confirm() {
    startTransition(async () => {
      const result = await removeMemberAction(audienceId, memberId);

      if (!result.ok) {
        toast.error(result.message);
        return;
      }

      toast.success(`${fullName} removed`);
      router.refresh();
    });
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-muted-foreground hover:text-destructive"
          aria-label={`Remove ${fullName}`}
        >
          <Trash2Icon aria-hidden className="size-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remove {fullName}?</AlertDialogTitle>
          <AlertDialogDescription>
            They come off this list for every campaign that targets it. Views and responses they
            have already recorded are kept.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Keep them</AlertDialogCancel>
          <AlertDialogAction disabled={pending} onClick={confirm}>
            {pending ? "Removing…" : "Remove"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
