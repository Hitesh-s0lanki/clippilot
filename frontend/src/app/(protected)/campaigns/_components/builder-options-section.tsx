"use client";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderOptionFields } from "./builder-option-fields";

export interface BuilderOptionsSectionProps {
  form: CampaignForm;
}

/**
 * Section 4 - the two response options.
 *
 * Exactly two, fixed: the brief's interaction is a binary choice, and the
 * publish contract rejects any other count. There is no add or remove here on
 * purpose.
 */
export function BuilderOptionsSection({ form }: BuilderOptionsSectionProps) {
  const { values, errors, setOption, revalidate } = form;

  return (
    <>
      {errors["experience.options"] ? (
        <p role="alert" className="text-sm font-medium text-destructive">
          {errors["experience.options"]}
        </p>
      ) : null}

      <div className="space-y-4">
        {values.options.map((option) => (
          <BuilderOptionFields
            key={option.position}
            option={option}
            errors={errors}
            onChange={setOption}
            onBlur={revalidate}
          />
        ))}
      </div>

      <p className="text-xs leading-relaxed text-muted-foreground">
        Both buttons are rendered at equal weight in the preview. Making one of them look like the
        primary action would bias the response and distort the metric you are measuring.
      </p>
    </>
  );
}
