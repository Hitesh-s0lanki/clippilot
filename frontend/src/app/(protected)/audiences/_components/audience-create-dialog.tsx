"use client";

import { PlusIcon } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { createAudienceAction } from "@/lib/actions/audience-actions";

/**
 * Creates an empty list and goes straight to it.
 *
 * Naming is the only step here. People are added on the audience's own screen,
 * where the CSV upload and the segment breakdown live - asking for a name and
 * a file in one dialog would put the import's partial-success report somewhere
 * it has no room to be read.
 */
export function AudienceCreateDialog() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      const result = await createAudienceAction({
        name: name.trim(),
        description: description.trim() || null,
      });

      if (!result.ok) {
        setError(result.fieldErrors.name ?? result.message);
        return;
      }

      toast.success(`“${result.data.name}” created`);
      setOpen(false);
      setName("");
      setDescription("");
      router.push(`/audiences/${result.data.id}`);
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <PlusIcon aria-hidden />
          New audience
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>New audience</DialogTitle>
            <DialogDescription>
              Name the list. You will add people to it on the next screen.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2">
            <Label htmlFor="audience-name">Name</Label>
            <Input
              id="audience-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="HNI Investors — Metro"
              maxLength={120}
              required
              autoFocus
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? "audience-name-error" : undefined}
            />
            {error ? (
              <p id="audience-name-error" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience-description">Description (optional)</Label>
            <Textarea
              id="audience-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Where this list came from, and who is on it."
              maxLength={500}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={pending || name.trim().length === 0}>
              {pending ? "Creating…" : "Create audience"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
