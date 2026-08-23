"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { OBJECTIVE_HINTS, OBJECTIVE_LABELS } from "@/lib/campaign-labels";
import type { CampaignObjective } from "@/types/campaign";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderField } from "./builder-field";

export interface BuilderCampaignSectionProps {
  form: CampaignForm;
  /** Locked once published: the objective decides what past metrics mean. */
  objectiveLocked: boolean;
}

const OBJECTIVES = Object.keys(OBJECTIVE_LABELS) as CampaignObjective[];

/** Section 1 - name, description and the objective that picks the lead metric. */
export function BuilderCampaignSection({ form, objectiveLocked }: BuilderCampaignSectionProps) {
  const { values, errors, setField, revalidate } = form;

  return (
    <>
      <BuilderField
        field="name"
        label="Campaign name"
        required
        error={errors.name}
        hint="The only field a draft needs. It also has to be unique across your campaigns."
      >
        {(control) => (
          <Input
            {...control}
            className="h-9"
            value={values.name}
            maxLength={120}
            placeholder="Q3 SIP top-up nudge"
            onChange={(event) => setField("name", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>

      <BuilderField
        field="description"
        label="Description"
        error={errors.description}
        hint="Internal only. Recipients never see this."
      >
        {(control) => (
          <Textarea
            {...control}
            rows={2}
            maxLength={500}
            value={values.description}
            placeholder="Who this is for and why it is going out."
            onChange={(event) => setField("description", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>

      <BuilderField
        field="objective"
        label="Objective"
        error={errors.objective}
        hint={
          objectiveLocked
            ? "Locked: the objective decides what the recorded metrics mean, so it cannot change after publishing."
            : OBJECTIVE_HINTS[values.objective]
        }
      >
        {(control) => (
          <Select
            value={values.objective}
            disabled={objectiveLocked}
            onValueChange={(value) => setField("objective", value as CampaignObjective)}
          >
            <SelectTrigger {...control} className="h-9 w-full sm:w-72">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {OBJECTIVES.map((objective) => (
                <SelectItem key={objective} value={objective}>
                  {OBJECTIVE_LABELS[objective]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </BuilderField>
    </>
  );
}
