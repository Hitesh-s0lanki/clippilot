"use client";

import { LoaderCircleIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { PreviewOption } from "@/types/preview";

export interface PreviewOptionsProps {
  options: PreviewOption[];
  /** The option currently being recorded, if any. */
  submittingId: string | null;
  disabled: boolean;
  onChoose: (option: PreviewOption) => void;
}

/**
 * The two answers.
 *
 * Both are rendered at identical weight - same variant, same size, same width.
 * Making one of them the primary button would push the response toward it and
 * quietly corrupt the only metric this campaign exists to collect. Targets are
 * comfortably past the 44px minimum, and spaced, because this is the one
 * screen that is opened on a phone from an email.
 */
export function PreviewOptions({ options, submittingId, disabled, onChoose }: PreviewOptionsProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {options.map((option) => (
        <Button
          key={option.id}
          type="button"
          variant="outline"
          disabled={disabled}
          onClick={() => onChoose(option)}
          className="h-auto min-h-12 w-full justify-center px-4 py-3 text-base whitespace-normal"
        >
          {submittingId === option.id ? (
            <LoaderCircleIcon data-icon="inline-start" className="animate-spin" />
          ) : null}
          {option.label}
        </Button>
      ))}
    </div>
  );
}
