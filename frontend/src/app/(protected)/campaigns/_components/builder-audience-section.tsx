"use client";

import Link from "next/link";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCount } from "@/lib/format";
import type { AudienceSummary } from "@/types/audience";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderField } from "./builder-field";

export interface BuilderAudienceSectionProps {
  form: CampaignForm;
  /** Every list on the account, read on the server by the page above. */
  audiences: AudienceSummary[];
}

/**
 * Section 2 - which list receives the campaign.
 *
 * A selection, not an editor. An audience is account-level and any number of
 * campaigns can point at the same one, so editing people here would edit them
 * for every other campaign targeting that list - which is exactly the mistake
 * a builder that owned its own rows used to invite.
 */
export function BuilderAudienceSection({ form, audiences }: BuilderAudienceSectionProps) {
  const { values, errors, setField, revalidate } = form;
  const selected = audiences.find((audience) => audience.id === values.audience_id);

  if (audiences.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border px-4 py-6 text-center">
        <p className="text-sm font-medium">No audiences yet</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-pretty text-muted-foreground">
          A campaign is sent to a list of people. Build one — a single customer is a list of one —
          and it will be selectable here and reusable by every other campaign.
        </p>
        <Link
          href="/audiences"
          className="mt-3 inline-block text-sm font-medium underline underline-offset-4"
        >
          Create an audience
        </Link>
      </div>
    );
  }

  return (
    <>
      <BuilderField
        field="audience_id"
        label="Audience"
        error={errors.audience_id}
        hint="The list this campaign is sent to. Each member gets their own link, resolved with their own name."
      >
        {(control) => (
          <Select
            value={values.audience_id}
            onValueChange={(value) => {
              setField("audience_id", value);
              revalidate();
            }}
          >
            <SelectTrigger {...control} className="h-9 w-full">
              <SelectValue placeholder="Choose an audience" />
            </SelectTrigger>
            <SelectContent>
              {audiences.map((audience) => (
                <SelectItem key={audience.id} value={audience.id}>
                  {audience.name} · {formatCount(audience.member_count)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </BuilderField>

      {selected ? (
        <p className="text-xs text-muted-foreground">
          {selected.member_count === 0
            ? "This list is empty, so the campaign cannot be published yet."
            : `${formatCount(selected.member_count)} people will receive this campaign.`}{" "}
          <Link href="/audiences" className="underline underline-offset-4">
            Manage lists
          </Link>
        </p>
      ) : null}
    </>
  );
}
