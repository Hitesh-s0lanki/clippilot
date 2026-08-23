"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BUDGET_TYPE_LABELS, PACING_LABELS } from "@/lib/campaign-labels";
import type { BudgetType, Pacing } from "@/types/campaign";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderField } from "./builder-field";

export interface BuilderDeliverySectionProps {
  form: CampaignForm;
}

const BUDGET_TYPES = Object.keys(BUDGET_TYPE_LABELS) as BudgetType[];
const CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SGD"];

/**
 * Section 7 - budget, caps and pacing.
 *
 * Amounts are typed in major units and converted to the integer minor units
 * the API stores, so nothing here ever puts a float on the wire. The budget
 * fields stay hidden until a budget type is chosen: an amount box with no type
 * is a rejection waiting to happen.
 */
export function BuilderDeliverySection({ form }: BuilderDeliverySectionProps) {
  const { values, errors, setField, revalidate } = form;
  const budgeted = values.budget_type !== "NONE";

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        <BuilderField field="budget.budget_type" label="Budget type">
          {(control) => (
            <Select
              value={values.budget_type}
              onValueChange={(value) => setField("budget_type", value as BudgetType)}
            >
              <SelectTrigger {...control} className="h-9 w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BUDGET_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {BUDGET_TYPE_LABELS[type]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </BuilderField>

        {budgeted ? (
          <BuilderField field="budget.currency" label="Currency">
            {(control) => (
              <Select
                value={values.currency}
                onValueChange={(value) => setField("currency", value)}
              >
                <SelectTrigger {...control} className="h-9 w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCIES.map((currency) => (
                    <SelectItem key={currency} value={currency}>
                      {currency}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </BuilderField>
        ) : null}
      </div>

      {budgeted ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <BuilderField
            field="budget.budget_amount_minor"
            label="Budget amount"
            required
            error={errors["budget.budget_amount_minor"]}
            hint={`In ${values.currency}, e.g. 50000.`}
          >
            {(control) => (
              <Input
                {...control}
                type="number"
                min={0}
                step="0.01"
                className="h-9"
                value={values.budget_amount}
                onChange={(event) => setField("budget_amount", event.target.value)}
                onBlur={revalidate}
              />
            )}
          </BuilderField>

          <BuilderField
            field="budget.spend_cap_minor"
            label="Spend cap"
            error={errors["budget.spend_cap_minor"]}
            hint="Optional hard ceiling. Cannot be below the budget amount."
          >
            {(control) => (
              <Input
                {...control}
                type="number"
                min={0}
                step="0.01"
                className="h-9"
                value={values.spend_cap}
                onChange={(event) => setField("spend_cap", event.target.value)}
                onBlur={revalidate}
              />
            )}
          </BuilderField>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <BuilderField
          field="delivery.pacing"
          label="Pacing"
          error={errors["delivery.pacing"]}
          hint="Accelerated needs an end date."
        >
          {(control) => (
            <Select
              value={values.pacing}
              onValueChange={(value) => setField("pacing", value as Pacing)}
            >
              <SelectTrigger {...control} className="h-9 w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(PACING_LABELS) as Pacing[]).map((pacing) => (
                  <SelectItem key={pacing} value={pacing}>
                    {PACING_LABELS[pacing]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </BuilderField>

        <BuilderField field="delivery.send_cap_total" label="Total send cap">
          {(control) => (
            <Input
              {...control}
              type="number"
              min={1}
              className="h-9"
              value={values.send_cap_total}
              onChange={(event) => setField("send_cap_total", event.target.value)}
              onBlur={revalidate}
            />
          )}
        </BuilderField>

        <BuilderField
          field="delivery.send_cap_per_day"
          label="Daily send cap"
          error={errors["delivery.send_cap_per_day"]}
        >
          {(control) => (
            <Input
              {...control}
              type="number"
              min={1}
              className="h-9"
              value={values.send_cap_per_day}
              onChange={(event) => setField("send_cap_per_day", event.target.value)}
              onBlur={revalidate}
            />
          )}
        </BuilderField>
      </div>
    </>
  );
}
