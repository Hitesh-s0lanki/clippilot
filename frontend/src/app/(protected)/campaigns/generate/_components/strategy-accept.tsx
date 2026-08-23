"use client";

import { CheckIcon, RotateCcwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCount } from "@/lib/format";
import type { AudienceSummary } from "@/types/audience";

export interface StrategyAcceptProps {
  audiences: AudienceSummary[];
  audienceId: string;
  pending: boolean;
  onAudienceChange: (audienceId: string) => void;
  onAccept: () => void;
  onDiscard: () => void;
}

/**
 * The one thing the agent cannot decide, and the commit.
 *
 * An audience is picked here rather than generated: the agent has no idea
 * which of your lists this is for, and guessing would be worse than asking.
 * Nothing is written until Create is pressed, so discarding costs only the run.
 */
export function StrategyAccept({
  audiences,
  audienceId,
  pending,
  onAudienceChange,
  onAccept,
  onDiscard,
}: StrategyAcceptProps) {
  const selected = audiences.find((audience) => audience.id === audienceId);

  return (
    <div className="sticky bottom-0 z-20 border-t border-border bg-background/95 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-56 flex-1 space-y-1.5">
          <Label htmlFor="draft-audience">Send it to</Label>
          <Select value={audienceId} onValueChange={onAudienceChange}>
            <SelectTrigger id="draft-audience" className="h-9 w-full">
              <SelectValue placeholder="Choose an audience" />
            </SelectTrigger>
            <SelectContent>
              {audiences.map((audience) => (
                <SelectItem key={audience.id} value={audience.id}>
                  {audience.name} · {formatCount(audience.member_count)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button type="button" variant="ghost" size="lg" disabled={pending} onClick={onDiscard}>
          <RotateCcwIcon data-icon="inline-start" />
          Start over
        </Button>

        <Button type="button" size="lg" disabled={pending || !selected} onClick={onAccept}>
          <CheckIcon data-icon="inline-start" />
          {pending ? "Creating…" : "Create campaign"}
        </Button>
      </div>
    </div>
  );
}
