"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CTA_LABELS, type CallToAction } from "@/types/campaign";
import type { UploadConfig } from "@/types/upload";

import type { AdForm } from "../_hooks/use-ad-form";
import { BuilderField } from "./builder-field";
import { BuilderMessageField } from "./builder-message-field";
import { BuilderVideoField } from "./builder-video-field";

export interface BuilderAdSectionProps {
  form: AdForm;
  uploads: UploadConfig;
  /** Resolves {{campaign_name}} in the message preview. */
  campaignName: string;
}

const CTA_OPTIONS = Object.keys(CTA_LABELS) as CallToAction[];

/**
 * One ad's fields: its video, its copy and its call to action.
 *
 * A flat form rather than an accordion. The campaign's settings are configured
 * once and live on their own screen; an ad is eight fields, and hiding eight
 * fields behind collapsible headers costs more clicks than it saves scrolling.
 */
export function BuilderAdSection({ form, uploads, campaignName }: BuilderAdSectionProps) {
  const { values, errors, setField, revalidate } = form;

  return (
    <>
      <BuilderField
        field="name"
        label="Ad name"
        error={errors["name"]}
        hint="Internal only, and unique within the campaign. Name it after the angle it takes."
      >
        {(control) => (
          <Input
            {...control}
            className="h-9"
            maxLength={120}
            value={values.name}
            placeholder="Paused-SIP cost of waiting"
            onChange={(event) => setField("name", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>

      <BuilderVideoField form={form} uploads={uploads} />

      <BuilderField
        field="poster_url"
        label="Poster image"
        error={errors["poster_url"]}
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
        field="headline"
        label="Headline"
        error={errors["headline"]}
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

      <BuilderField
        field="description"
        label="Description"
        error={errors["description"]}
        hint="One supporting line under the headline. The customer reads this, unlike the campaign description."
      >
        {(control) => (
          <Input
            {...control}
            className="h-9"
            maxLength={500}
            value={values.description}
            placeholder="Reviewed by an advisor, matched to your risk profile."
            onChange={(event) => setField("description", event.target.value)}
            onBlur={revalidate}
          />
        )}
      </BuilderField>

      <BuilderField
        field="cta"
        label="Call to action"
        error={errors["cta"]}
        hint="Names what this ad asks for, and fills in the positive button's label when you leave it blank."
      >
        {(control) => (
          <Select
            value={values.cta}
            onValueChange={(value) => setField("cta", value as CallToAction)}
          >
            <SelectTrigger {...control} className="h-9 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CTA_OPTIONS.map((cta) => (
                <SelectItem key={cta} value={cta}>
                  {CTA_LABELS[cta]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </BuilderField>

      <BuilderMessageField
        value={values.personalised_message}
        error={errors["personalised_message"]}
        campaignName={campaignName}
        onChange={(value) => setField("personalised_message", value)}
        onBlur={revalidate}
      />
    </>
  );
}
