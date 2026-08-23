"use client";

import { UploadIcon } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { addMembersAction } from "@/lib/actions/audience-actions";

import { MAX_MEMBERS_PER_UPLOAD, parseMemberCsv } from "../_lib/audience-csv";
import type { ParsedMembers } from "../_lib/audience-csv";
import { ImportSummary } from "./import-summary";
import { SampleCsvLink } from "./sample-csv-link";

export interface MemberImportDialogProps {
  audienceId: string;
}

/**
 * Uploads a CSV of people.
 *
 * The file is parsed and reported on *before* anything is sent, so the user
 * sees which rows will not land while they can still fix the file. Sending
 * first and explaining afterwards is how an import quietly loses two rows out
 * of ten.
 *
 * Only a name column is required. Every other column is optional and any it
 * does not recognise is ignored rather than refused.
 */
export function MemberImportDialog({ audienceId }: MemberImportDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [parsed, setParsed] = useState<ParsedMembers | null>(null);
  const [pending, startTransition] = useTransition();

  async function read(file: File | undefined) {
    if (!file) {
      setParsed(null);
      return;
    }

    const result = parseMemberCsv(await file.text());
    setParsed(
      result.rows.length > MAX_MEMBERS_PER_UPLOAD
        ? { ...result, rows: result.rows.slice(0, MAX_MEMBERS_PER_UPLOAD) }
        : result,
    );
  }

  function submit() {
    if (!parsed || parsed.rows.length === 0) return;

    startTransition(async () => {
      const result = await addMembersAction(
        audienceId,
        parsed.rows.map((row) => row.member),
      );

      if (!result.ok) {
        toast.error(result.message);
        return;
      }

      const { added, skipped } = result.data;
      toast.success(
        skipped.length === 0
          ? `${added} added`
          : `${added} added, ${skipped.length} skipped as duplicates`,
      );
      setOpen(false);
      setParsed(null);
      router.refresh();
    });
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setParsed(null);
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline">
          <UploadIcon aria-hidden />
          Upload CSV
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload people</DialogTitle>
          <DialogDescription>
            A CSV with a header row. Only <code>full_name</code> is required — <code>email</code>,{" "}
            <code>phone</code>, <code>age</code>, <code>gender</code>, <code>city</code>,{" "}
            <code>country</code> and <code>external_ref</code> are all optional.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <Label htmlFor="member-csv">CSV file</Label>
            <SampleCsvLink />
          </div>
          <Input
            id="member-csv"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => void read(event.target.files?.[0])}
          />
          <p className="text-xs text-muted-foreground">
            Not sure about the format? Download the sample, replace the rows and upload it back.
          </p>
        </div>

        {parsed?.error ? (
          <p className="text-sm text-destructive">{parsed.error}</p>
        ) : parsed ? (
          <ImportSummary added={parsed.rows.length} skipped={parsed.skipped} />
        ) : null}

        <DialogFooter>
          <Button onClick={submit} disabled={pending || !parsed || parsed.rows.length === 0}>
            {pending ? "Adding…" : `Add ${parsed?.rows.length ?? 0}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
