"use client";

import { Accordion } from "@/components/ui/accordion";
import type { AudienceSummary } from "@/types/audience";
import type { Campaign } from "@/types/campaign";

import { useCampaignForm } from "../_hooks/use-campaign-form";
import { BUILDER_SECTIONS, sectionForField } from "../_lib/campaign-form-sections";
import { BuilderActions } from "./builder-actions";
import { BuilderAudienceSection } from "./builder-audience-section";
import { BuilderCampaignSection } from "./builder-campaign-section";
import { BuilderComplianceSection } from "./builder-compliance-section";
import { BuilderDeliverySection } from "./builder-delivery-section";
import { BuilderIssuesAlert } from "./builder-issues-alert";
import { BuilderScheduleSection } from "./builder-schedule-section";
import { BuilderSection } from "./builder-section";
import { BuilderTrackingSection } from "./builder-tracking-section";

export interface CampaignBuilderProps {
  /** Absent when creating. Present, the form edits it in place. */
  campaign?: Campaign;
  /** Every list on the account, read on the server by the page above. */
  audiences: AudienceSummary[];
}

/**
 * The campaign form: everything except the creatives.
 *
 * Ads live on their own screen. A campaign is configured once - objective,
 * audience, schedule, budget, compliance, tracking - and then holds up to five
 * creatives that are added, edited and switched on individually. Carrying both
 * in one form meant scrolling past a dozen settings to reach the video, and
 * meant a second creative had nowhere to go.
 *
 * The orchestrator owns state and section order and nothing else - each
 * section renders its own fields and knows nothing about submitting, and the
 * behaviour lives in `use-campaign-form`.
 */
export function CampaignBuilder({ campaign, audiences }: CampaignBuilderProps) {
  const form = useCampaignForm({ campaign });
  const errorFields = Object.keys(form.errors);

  const errorsBySection = errorFields.reduce<Record<string, number>>((counts, field) => {
    const section = sectionForField(field);
    counts[section] = (counts[section] ?? 0) + 1;
    return counts;
  }, {});

  return (
    <form
      noValidate
      onSubmit={(event) => {
        // Enter inside a text field must not fire whichever button is first.
        // Saving is an explicit act here, and one of the two buttons is a
        // publish.
        event.preventDefault();
      }}
      className="space-y-6"
    >
      {form.summary ? <BuilderIssuesAlert summary={form.summary} fields={errorFields} /> : null}

      <Accordion
        type="multiple"
        value={form.openSections}
        onValueChange={form.setOpenSections}
        className="rounded-xl bg-card px-5 ring-1 ring-foreground/10"
      >
        {BUILDER_SECTIONS.map((section) => (
          <BuilderSection
            key={section.id}
            section={section}
            errorCount={errorsBySection[section.id] ?? 0}
          >
            {section.id === "campaign" ? (
              <BuilderCampaignSection
                form={form}
                objectiveLocked={Boolean(campaign?.published_at)}
              />
            ) : null}
            {section.id === "audience" ? (
              <BuilderAudienceSection form={form} audiences={audiences} />
            ) : null}
            {section.id === "schedule" ? <BuilderScheduleSection form={form} /> : null}
            {section.id === "compliance" ? <BuilderComplianceSection form={form} /> : null}
            {section.id === "delivery" ? <BuilderDeliverySection form={form} /> : null}
            {section.id === "tracking" ? <BuilderTrackingSection form={form} /> : null}
          </BuilderSection>
        ))}
      </Accordion>

      <BuilderActions
        status={campaign?.status ?? null}
        pending={form.pending}
        dirty={form.dirty}
        previewHref={campaign ? `/campaigns/${campaign.id}/preview` : undefined}
        onSaveDraft={form.saveDraft}
        onPublish={form.publish}
      />
    </form>
  );
}
