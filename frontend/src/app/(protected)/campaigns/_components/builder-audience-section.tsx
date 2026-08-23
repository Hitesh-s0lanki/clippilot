"use client";

import { PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { AUDIENCE_TYPE_LABELS } from "@/lib/campaign-labels";
import type { AudienceType } from "@/types/campaign";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderRecipientRow } from "./builder-recipient-row";

export interface BuilderAudienceSectionProps {
  form: CampaignForm;
}

/**
 * Section 2 - who receives the campaign.
 *
 * The audience type is a real constraint, not a label: the API rejects a
 * `SINGLE` campaign that carries two recipients, so switching to a list is
 * what the "Add recipient" button does first.
 */
export function BuilderAudienceSection({ form }: BuilderAudienceSectionProps) {
  const { values, errors, setField, setRecipient, addRecipient, removeRecipient, revalidate } =
    form;

  const isList = values.audience_type === "LIST";

  return (
    <>
      <div className="space-y-1.5">
        <Label id="audience-type-label">Audience</Label>
        <ToggleGroup
          type="single"
          value={values.audience_type}
          aria-labelledby="audience-type-label"
          onValueChange={(value) => {
            if (!value) return;
            setField("audience_type", value as AudienceType);
            if (value === "SINGLE" && values.recipients.length > 1) {
              setField("recipients", values.recipients.slice(0, 1));
            }
          }}
        >
          <ToggleGroupItem value="SINGLE">{AUDIENCE_TYPE_LABELS.SINGLE}</ToggleGroupItem>
          <ToggleGroupItem value="LIST">{AUDIENCE_TYPE_LABELS.LIST}</ToggleGroupItem>
        </ToggleGroup>
        <p className="text-xs text-muted-foreground">
          {isList
            ? "Each recipient gets their own preview link, resolved with their own name."
            : "One recipient. Switch to a list to send the same journey to several people."}
        </p>
      </div>

      {errors.recipients ? (
        <p role="alert" className="text-sm font-medium text-destructive">
          {errors.recipients}
        </p>
      ) : null}

      <ul className="space-y-3">
        {values.recipients.map((recipient, index) => (
          <BuilderRecipientRow
            key={index}
            index={index}
            recipient={recipient}
            errors={errors}
            removable={isList && values.recipients.length > 1}
            onChange={setRecipient}
            onRemove={removeRecipient}
            onBlur={revalidate}
          />
        ))}
      </ul>

      <Button type="button" variant="outline" size="lg" onClick={addRecipient}>
        <PlusIcon data-icon="inline-start" />
        Add recipient
      </Button>
    </>
  );
}
