"use client";

import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import { fieldErrorId, fieldId } from "../_lib/field-id";

export interface FieldControl {
  id: string;
  "aria-invalid": boolean;
  "aria-describedby": string | undefined;
}

export interface BuilderFieldProps {
  /** Dotted path, e.g. `ads.0.options.1.label`. Drives every id here. */
  field: string;
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  className?: string;
  /** Receives the ids and ARIA wiring, so no call site repeats them. */
  children: (control: FieldControl) => ReactNode;
}

/**
 * One labelled control, with its hint and its error.
 *
 * A render prop rather than a wrapper, because the accessible wiring is the
 * whole point: the label's `htmlFor`, the input's `aria-describedby` and the
 * message's `id` have to agree, and deriving all three from the field path
 * makes disagreeing impossible. The error is `role="alert"` so it is announced
 * when it appears rather than only being red.
 */
export function BuilderField({
  field,
  label,
  hint,
  error,
  required,
  className,
  children,
}: BuilderFieldProps) {
  const id = fieldId(field);
  const errorId = fieldErrorId(field);
  const hintId = `${id}-hint`;

  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(" ");

  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={id}>
        {label}
        {required ? (
          <span className="text-destructive" title="Required to publish">
            *
          </span>
        ) : null}
      </Label>

      {children({
        id,
        "aria-invalid": Boolean(error),
        "aria-describedby": describedBy || undefined,
      })}

      {error ? (
        <p id={errorId} role="alert" className="text-sm font-medium text-destructive">
          {error}
        </p>
      ) : null}
      {hint ? (
        <p id={hintId} className="text-xs leading-relaxed text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
