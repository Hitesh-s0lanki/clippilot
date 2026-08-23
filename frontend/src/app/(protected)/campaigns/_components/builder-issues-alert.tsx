"use client";

import { TriangleAlertIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import { describeField } from "../_lib/campaign-form-sections";
import { fieldId } from "../_lib/field-id";

export interface BuilderIssuesAlertProps {
  /** The message from the failed submit, client-side or from the API. */
  summary: string;
  fields: string[];
}

/**
 * Every unmet requirement, listed once, above the form.
 *
 * The fields are marked inline as well, but inline alone is not enough in an
 * accordion: half of them can be inside a section that is scrolled past or
 * folded shut. Each entry is a link to its own field, so the list is a way to
 * get there rather than only a list.
 */
export function BuilderIssuesAlert({ summary, fields }: BuilderIssuesAlertProps) {
  return (
    <Alert variant="destructive" aria-live="assertive">
      <TriangleAlertIcon />
      <AlertTitle>{summary}</AlertTitle>
      {fields.length > 0 ? (
        <AlertDescription>
          <ul className="flex flex-wrap gap-x-2 gap-y-1">
            {fields.map((field) => (
              <li key={field}>
                <a
                  href={`#${fieldId(field)}`}
                  className="rounded underline underline-offset-2 hover:no-underline focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
                >
                  {describeField(field)}
                </a>
              </li>
            ))}
          </ul>
        </AlertDescription>
      ) : null}
    </Alert>
  );
}
