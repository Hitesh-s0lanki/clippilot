"use client";

import { UserPlusIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { addMembersAction } from "@/lib/actions/audience-actions";
import type { AudienceMemberInput } from "@/types/audience";

import { EMPTY_MEMBER_FORM, MemberAddFields } from "./member-add-fields";
import type { MemberFormValues } from "./member-add-fields";

export interface MemberAddDialogProps {
  audienceId: string;
}

/**
 * Adds one person by hand.
 *
 * Every field but the name is optional here for the same reason it is optional
 * in the CSV: you add who you know about with what you know about them, and a
 * form that demands a phone number gets an invented one.
 */
export function MemberAddDialog({ audienceId }: MemberAddDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<MemberFormValues>(EMPTY_MEMBER_FORM);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function set(field: keyof MemberFormValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      const result = await addMembersAction(audienceId, [toInput(values)]);

      if (!result.ok) {
        setError(result.message);
        return;
      }
      // The API skips rather than fails, so a rejected row arrives as a
      // successful call that added nobody. Read the reason out of it.
      if (result.data.added === 0) {
        setError(result.data.skipped[0]?.reason ?? "That person could not be added.");
        return;
      }

      toast.success(`${values.full_name.trim()} added`);
      setOpen(false);
      setValues(EMPTY_MEMBER_FORM);
      router.refresh();
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <UserPlusIcon aria-hidden />
          Add person
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Add a person</DialogTitle>
            <DialogDescription>
              Only the name is required. Anything else you fill in becomes a segment you can target.
            </DialogDescription>
          </DialogHeader>

          <MemberAddFields values={values} onChange={set} />

          {error ? <p className="text-sm text-destructive">{error}</p> : null}

          <DialogFooter>
            <Button type="submit" disabled={pending || values.full_name.trim().length === 0}>
              {pending ? "Adding…" : "Add person"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/** Form strings to the wire shape. Empty is null, never "" - the API rejects "". */
function toInput(values: MemberFormValues): AudienceMemberInput {
  const age = Number.parseInt(values.age, 10);

  return {
    full_name: values.full_name.trim(),
    email: values.email.trim() || null,
    // Spreadsheet separators are stripped for the same reason the importer
    // strips them: the server's pattern is digits only.
    phone: values.phone.replace(/[\s().-]/g, "") || null,
    age: Number.isFinite(age) ? age : null,
    gender: values.gender,
    city: values.city.trim() || null,
    country: values.country.trim() || null,
    external_ref: values.external_ref.trim() || null,
  };
}
