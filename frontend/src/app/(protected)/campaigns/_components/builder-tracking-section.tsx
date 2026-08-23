"use client";

import { Input } from "@/components/ui/input";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderField } from "./builder-field";

export interface BuilderTrackingSectionProps {
  form: CampaignForm;
}

const FIELDS = [
  { key: "utm_source", label: "utm_source", placeholder: "trustvid" },
  { key: "utm_medium", label: "utm_medium", placeholder: "interactive-video" },
  { key: "utm_campaign", label: "utm_campaign", placeholder: "sip-top-up-q3" },
  { key: "utm_content", label: "utm_content", placeholder: "option-1" },
] as const;

/**
 * Section 8 - the UTM parameters appended to follow-up links.
 *
 * Appended at click time without overwriting parameters the destination
 * already carries, so a link that already has its own tracking keeps it.
 */
export function BuilderTrackingSection({ form }: BuilderTrackingSectionProps) {
  const { values, errors, setField, revalidate } = form;

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        {FIELDS.map(({ key, label, placeholder }) => (
          <BuilderField
            key={key}
            field={`tracking.${key}`}
            label={label}
            error={errors[`tracking.${key}`]}
          >
            {(control) => (
              <Input
                {...control}
                className="h-9 font-mono text-sm"
                maxLength={80}
                value={values[key]}
                placeholder={placeholder}
                onChange={(event) => setField(key, event.target.value)}
                onBlur={revalidate}
              />
            )}
          </BuilderField>
        ))}
      </div>

      <BuilderField
        field="tracking.external_ref"
        label="External reference"
        error={errors["tracking.external_ref"]}
        hint="Your own id for this campaign in another system."
      >
        {(control) => (
          <Input
            {...control}
            className="h-9"
            maxLength={120}
            value={values.external_ref}
            placeholder="CRM-CAMP-2026-08"
            onChange={(event) => setField("external_ref", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>
    </>
  );
}
