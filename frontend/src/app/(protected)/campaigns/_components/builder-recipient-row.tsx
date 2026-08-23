"use client";

import { Trash2Icon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { RecipientFormValues } from "../_lib/campaign-form-values";
import type { FieldErrors } from "../_lib/campaign-form-validation";

import { BuilderField } from "./builder-field";

export interface BuilderRecipientRowProps {
  index: number;
  recipient: RecipientFormValues;
  errors: FieldErrors;
  /** Hidden for a single-recipient campaign, where there is nothing to remove. */
  removable: boolean;
  onChange: (index: number, patch: Partial<RecipientFormValues>) => void;
  onRemove: (index: number) => void;
  onBlur: () => void;
}

/**
 * One recipient.
 *
 * `customer_name` is the field that resolves `{{customer_name}}` in the
 * message, so it leads the row and is the only required one - email, phone and
 * the CRM reference are there for the integration, not for the preview.
 */
export function BuilderRecipientRow({
  index,
  recipient,
  errors,
  removable,
  onChange,
  onRemove,
  onBlur,
}: BuilderRecipientRowProps) {
  return (
    <li className="rounded-lg border border-border p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-muted-foreground">Recipient {index + 1}</p>
        {removable ? (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={`Remove recipient ${index + 1}`}
            onClick={() => onRemove(index)}
          >
            <Trash2Icon />
          </Button>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <BuilderField
          field={`recipients.${index}.customer_name`}
          label="Customer name"
          required
          error={errors[`recipients.${index}.customer_name`]}
          hint="Replaces {{customer_name}} in the message."
        >
          {(control) => (
            <Input
              {...control}
              className="h-9"
              value={recipient.customer_name}
              maxLength={80}
              placeholder="Priya Sharma"
              onChange={(event) => onChange(index, { customer_name: event.target.value })}
              onBlur={onBlur}
            />
          )}
        </BuilderField>

        <BuilderField
          field={`recipients.${index}.email`}
          label="Email"
          error={errors[`recipients.${index}.email`]}
        >
          {(control) => (
            <Input
              {...control}
              type="email"
              className="h-9"
              value={recipient.email}
              placeholder="priya@example.com"
              onChange={(event) => onChange(index, { email: event.target.value })}
              onBlur={onBlur}
            />
          )}
        </BuilderField>

        <BuilderField
          field={`recipients.${index}.phone`}
          label="Phone"
          error={errors[`recipients.${index}.phone`]}
          hint="Digits only, optionally starting with +."
        >
          {(control) => (
            <Input
              {...control}
              type="tel"
              className="h-9"
              value={recipient.phone}
              placeholder="+919876543210"
              onChange={(event) => onChange(index, { phone: event.target.value })}
              onBlur={onBlur}
            />
          )}
        </BuilderField>

        <BuilderField
          field={`recipients.${index}.external_ref`}
          label="CRM reference"
          error={errors[`recipients.${index}.external_ref`]}
        >
          {(control) => (
            <Input
              {...control}
              className="h-9"
              value={recipient.external_ref}
              placeholder="CRM-10428"
              onChange={(event) => onChange(index, { external_ref: event.target.value })}
              onBlur={onBlur}
            />
          )}
        </BuilderField>
      </div>
    </li>
  );
}
