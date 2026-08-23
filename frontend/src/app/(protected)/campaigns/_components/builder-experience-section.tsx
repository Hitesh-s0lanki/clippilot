"use client";

import { Input } from "@/components/ui/input";
import type { UploadConfig } from "@/types/upload";

import type { CampaignForm } from "../_hooks/use-campaign-form";
import { BuilderField } from "./builder-field";
import { BuilderMessageField } from "./builder-message-field";
import { BuilderVideoField } from "./builder-video-field";

export interface BuilderExperienceSectionProps {
  form: CampaignForm;
  uploads: UploadConfig;
}

/** Section 3 - the video and the copy wrapped around it. */
export function BuilderExperienceSection({ form, uploads }: BuilderExperienceSectionProps) {
  const { values, errors, setField, revalidate } = form;
  const firstRecipient = values.recipients[0]?.customer_name ?? "";

  return (
    <>
      <BuilderVideoField form={form} uploads={uploads} />

      <BuilderField
        field="experience.poster_url"
        label="Poster image"
        error={errors["experience.poster_url"]}
        hint="Shown before playback starts, and as the thumbnail on the dashboard."
      >
        {(control) => (
          <Input
            {...control}
            type="url"
            className="h-9"
            value={values.poster_url}
            placeholder="https://cdn.example.com/clips/sip-nudge.jpg"
            onChange={(event) => setField("poster_url", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>

      <BuilderField
        field="experience.headline"
        label="Headline"
        error={errors["experience.headline"]}
        hint="Sits above the video. Also supports {{customer_name}}."
      >
        {(control) => (
          <Input
            {...control}
            className="h-9"
            maxLength={80}
            value={values.headline}
            placeholder="A quick note about your portfolio"
            onChange={(event) => setField("headline", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>

      <BuilderMessageField
        value={values.personalised_message}
        error={errors["experience.personalised_message"]}
        customerName={firstRecipient}
        campaignName={values.name}
        onChange={(value) => setField("personalised_message", value)}
        onBlur={revalidate}
      />
    </>
  );
}
