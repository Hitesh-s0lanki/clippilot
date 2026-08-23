"use client";

import { SparklesIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export interface GenerateBriefFormProps {
  value: string;
  error: string | null;
  pending: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

const MIN_LENGTH = 10;

/**
 * One box.
 *
 * Everything else the agent needs - which business this is, its market, who it
 * competes with - it works out: a URL in the text is followed, a name is
 * searched for, and the competitive set is found rather than asked for.
 * Turning that into four fields made the user do the research the agent exists
 * to do, and made the empty state look like paperwork.
 */
export function GenerateBriefForm({
  value,
  error,
  pending,
  onChange,
  onSubmit,
}: GenerateBriefFormProps) {
  return (
    <form
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
      className="space-y-3"
    >
      <div className="space-y-1.5">
        <Label htmlFor="brief">What should this campaign do?</Label>
        <Textarea
          id="brief"
          rows={5}
          maxLength={2000}
          value={value}
          autoFocus
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "brief-error" : "brief-hint"}
          placeholder="Win back Acme Capital (acme.com) investors in India who paused their SIP this year. We want them to book a call with an advisor."
          onChange={(event) => onChange(event.target.value)}
        />
        {error ? (
          <p id="brief-error" role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : (
          <p id="brief-hint" className="text-xs text-muted-foreground">
            Mention your company or site if you want it read — otherwise the agent works from the
            market your goal describes.
          </p>
        )}
      </div>

      <Button
        type="submit"
        size="lg"
        disabled={pending || value.trim().length < MIN_LENGTH}
        className="w-full sm:w-auto"
      >
        <SparklesIcon data-icon="inline-start" />
        {pending ? "Researching…" : "Generate campaign"}
      </Button>
    </form>
  );
}
