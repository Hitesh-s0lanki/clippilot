"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatDateRange } from "@/lib/format";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { fromScheduleInput, timezoneOptions } from "../_lib/schedule";
import { BuilderField } from "./builder-field";

export interface BuilderScheduleSectionProps {
  form: CampaignForm;
}

/**
 * Section 5 - when the campaign runs.
 *
 * The two inputs are anchored to UTC rather than to the browser's zone, which
 * is what keeps a server-rendered builder from disagreeing with the hydrated
 * one. The line beneath renders the same window in the chosen display zone, so
 * the UTC values never have to be read cold.
 */
export function BuilderScheduleSection({ form }: BuilderScheduleSectionProps) {
  const { values, errors, setField, revalidate } = form;

  const start = fromScheduleInput(values.start_at);
  const end = fromScheduleInput(values.end_at);

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2">
        <BuilderField
          field="schedule.start_at"
          label="Start (UTC)"
          error={errors["schedule.start_at"]}
          hint="Leave blank to go live the moment it is published."
        >
          {(control) => (
            <Input
              {...control}
              type="datetime-local"
              className="h-9"
              value={values.start_at}
              onChange={(event) => setField("start_at", event.target.value)}
              onBlur={revalidate}
            />
          )}
        </BuilderField>

        <BuilderField
          field="schedule.end_at"
          label="End (UTC)"
          error={errors["schedule.end_at"]}
          hint="Leave blank to run until it is paused."
        >
          {(control) => (
            <Input
              {...control}
              type="datetime-local"
              className="h-9"
              value={values.end_at}
              onChange={(event) => setField("end_at", event.target.value)}
              onBlur={revalidate}
            />
          )}
        </BuilderField>
      </div>

      <BuilderField
        field="schedule.timezone"
        label="Display timezone"
        error={errors["schedule.timezone"]}
        hint="Changes how the window is shown to your team. Storage is always UTC."
      >
        {(control) => (
          <Select value={values.timezone} onValueChange={(value) => setField("timezone", value)}>
            <SelectTrigger {...control} className="h-9 w-full sm:w-72">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timezoneOptions(values.timezone).map((zone) => (
                <SelectItem key={zone} value={zone}>
                  {zone}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </BuilderField>

      <p className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
        In {values.timezone}, this campaign runs{" "}
        <span className="font-medium text-foreground">
          {formatDateRange(start, end, values.timezone)}
        </span>
        .
      </p>
    </>
  );
}
