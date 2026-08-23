"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { FOLLOW_UP_TYPE_LABELS, INTENT_LABELS } from "@/lib/campaign-labels";
import type { FollowUpType, OptionIntent } from "@/types/campaign";

import type { FieldErrors } from "../_lib/campaign-form-validation";
import type { OptionFormValues } from "../_lib/campaign-form-values";
import { BuilderField } from "./builder-field";

export interface BuilderOptionFieldsProps {
  option: OptionFormValues;
  errors: FieldErrors;
  onChange: (position: number, patch: Partial<OptionFormValues>) => void;
  onBlur: () => void;
}

const INTENTS = Object.keys(INTENT_LABELS) as OptionIntent[];

/**
 * One response option: its button label, what the click means, and the reply.
 *
 * The follow-up is either a message or a link, never both - the API rejects a
 * payload carrying the field that does not match the declared type - so the
 * segmented control swaps the input rather than showing two.
 */
export function BuilderOptionFields({
  option,
  errors,
  onChange,
  onBlur,
}: BuilderOptionFieldsProps) {
  const { position } = option;
  const prefix = `experience.options.${position}`;
  const isUrl = option.follow_up_type === "URL";

  return (
    <div className="rounded-lg border border-border p-4">
      <p className="mb-4 font-heading text-sm font-medium">Option {position}</p>

      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <BuilderField
            field={`${prefix}.label`}
            label="Button label"
            required
            error={errors[`${prefix}.label`]}
          >
            {(control) => (
              <Input
                {...control}
                className="h-9"
                maxLength={40}
                value={option.label}
                placeholder={position === 1 ? "Yes, tell me more" : "Not right now"}
                onChange={(event) => onChange(position, { label: event.target.value })}
                onBlur={onBlur}
              />
            )}
          </BuilderField>

          <BuilderField
            field={`${prefix}.intent`}
            label="Intent"
            error={errors[`${prefix}.intent`]}
            hint="Positive clicks are what a lead-capture campaign counts."
          >
            {(control) => (
              <Select
                value={option.intent}
                onValueChange={(value) => onChange(position, { intent: value as OptionIntent })}
              >
                <SelectTrigger {...control} className="h-9 w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INTENTS.map((intent) => (
                    <SelectItem key={intent} value={intent}>
                      {INTENT_LABELS[intent]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </BuilderField>
        </div>

        <div className="space-y-1.5">
          <Label id={`${prefix}-follow-up-label`}>Follow-up</Label>
          <ToggleGroup
            type="single"
            value={option.follow_up_type}
            aria-labelledby={`${prefix}-follow-up-label`}
            onValueChange={(value) => {
              if (!value) return;
              onChange(position, { follow_up_type: value as FollowUpType });
            }}
          >
            <ToggleGroupItem value="MESSAGE">{FOLLOW_UP_TYPE_LABELS.MESSAGE}</ToggleGroupItem>
            <ToggleGroupItem value="URL">{FOLLOW_UP_TYPE_LABELS.URL}</ToggleGroupItem>
          </ToggleGroup>
        </div>

        {isUrl ? (
          <BuilderField
            field={`${prefix}.follow_up_url`}
            label="Follow-up link"
            required
            error={errors[`${prefix}.follow_up_url`]}
            hint="The recipient is sent here after clicking. https only."
          >
            {(control) => (
              <Input
                {...control}
                type="url"
                className="h-9"
                value={option.follow_up_url}
                placeholder="https://example.com/book-a-call"
                onChange={(event) => onChange(position, { follow_up_url: event.target.value })}
                onBlur={onBlur}
              />
            )}
          </BuilderField>
        ) : (
          <BuilderField
            field={`${prefix}.follow_up_message`}
            label="Follow-up message"
            required
            error={errors[`${prefix}.follow_up_message`]}
            hint="Shown in place of the buttons once this option is clicked."
          >
            {(control) => (
              <Textarea
                {...control}
                rows={2}
                maxLength={500}
                value={option.follow_up_message}
                placeholder={
                  position === 1
                    ? "Brilliant - your advisor will call you within a day."
                    : "No problem. We will check back next quarter."
                }
                onChange={(event) => onChange(position, { follow_up_message: event.target.value })}
                onBlur={onBlur}
              />
            )}
          </BuilderField>
        )}
      </div>
    </div>
  );
}
