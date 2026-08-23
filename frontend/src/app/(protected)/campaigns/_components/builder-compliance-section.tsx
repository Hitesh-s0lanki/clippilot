"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { SPECIAL_CATEGORY_LABELS } from "@/lib/campaign-labels";
import type { SpecialCategory } from "@/types/campaign";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderField } from "./builder-field";

export interface BuilderComplianceSectionProps {
  form: CampaignForm;
}

const CATEGORIES = Object.keys(SPECIAL_CATEGORY_LABELS) as SpecialCategory[];

/** The API's own default copy for a financial-services campaign. */
const DEFAULT_DISCLAIMER =
  "Investments are subject to market risk. Read all scheme-related documents carefully. " +
  "This is not investment advice.";

/**
 * Section 6 - special category and the disclaimer that comes with it.
 *
 * Declaring a category makes the disclaimer mandatory, so choosing one offers
 * the standard wording rather than leaving an empty box and a rejection.
 */
export function BuilderComplianceSection({ form }: BuilderComplianceSectionProps) {
  const { values, errors, setField, revalidate } = form;
  const declared = values.special_category !== "NONE";

  return (
    <>
      <BuilderField
        field="compliance.special_category"
        label="Special category"
        error={errors["compliance.special_category"]}
        hint="Regulated subject matter. Recipients see a disclaimer beneath the video."
      >
        {(control) => (
          <Select
            value={values.special_category}
            onValueChange={(value) => {
              const category = value as SpecialCategory;
              setField("special_category", category);
              if (category === "FINANCIAL_PRODUCTS_SERVICES" && !values.disclaimer_text.trim()) {
                setField("disclaimer_text", DEFAULT_DISCLAIMER);
              }
            }}
          >
            <SelectTrigger {...control} className="h-9 w-full sm:w-80">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((category) => (
                <SelectItem key={category} value={category}>
                  {SPECIAL_CATEGORY_LABELS[category]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </BuilderField>

      {declared ? (
        <BuilderField
          field="compliance.disclaimer_text"
          label="Disclaimer"
          required
          error={errors["compliance.disclaimer_text"]}
          hint="Required once a category is declared. Rendered under the video, always visible."
        >
          {(control) => (
            <Textarea
              {...control}
              rows={3}
              maxLength={500}
              value={values.disclaimer_text}
              onChange={(event) => setField("disclaimer_text", event.target.value)}
              onBlur={revalidate}
            />
          )}
        </BuilderField>
      ) : null}
    </>
  );
}
