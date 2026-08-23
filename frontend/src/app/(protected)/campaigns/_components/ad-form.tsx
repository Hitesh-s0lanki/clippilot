"use client";

import type { CampaignAd } from "@/types/campaign";
import type { UploadConfig } from "@/types/upload";

import { useAdForm } from "../_hooks/use-ad-form";
import { AdFormActions } from "./ad-form-actions";
import { BuilderAdSection } from "./builder-ad-section";
import { BuilderIssuesAlert } from "./builder-issues-alert";
import { BuilderOptionsSection } from "./builder-options-section";
import { FormSection } from "./form-section";

export interface AdFormProps {
  campaignId: string;
  campaignName: string;
  /** Absent when adding; present, the form edits it in place. */
  ad?: CampaignAd;
  uploads: UploadConfig;
}

/**
 * One ad: the creative and its two response buttons.
 *
 * Flat and short, deliberately. The campaign's settings were configured on
 * their own screen and are not repeated here, which is the whole point of
 * splitting the two - an ad is a video, four lines of copy and two buttons, and
 * that fits on a screen without an accordion in front of it.
 */
export function AdForm({ campaignId, campaignName, ad, uploads }: AdFormProps) {
  const form = useAdForm({ campaignId, ad });
  const errorFields = Object.keys(form.errors);

  return (
    <form
      noValidate
      onSubmit={(event) => {
        // Enter inside a text field must not submit: saving is an explicit act.
        event.preventDefault();
      }}
      className="space-y-5"
    >
      {form.summary ? <BuilderIssuesAlert summary={form.summary} fields={errorFields} /> : null}

      <FormSection
        title="Creative"
        description="The video the customer watches, and the copy around it."
      >
        <BuilderAdSection form={form} uploads={uploads} campaignName={campaignName} />
      </FormSection>

      <FormSection title="Responses" description="The two buttons, and what each one replies with.">
        <BuilderOptionsSection form={form} />
      </FormSection>

      <AdFormActions
        campaignId={campaignId}
        adId={ad?.id}
        pending={form.pending}
        dirty={form.dirty}
        onSave={form.save}
      />
    </form>
  );
}
