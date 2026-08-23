"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, useTransition } from "react";
import { toast } from "sonner";

import {
  changeCampaignStatusAction,
  createCampaignAction,
  updateCampaignAction,
} from "@/lib/actions/campaign-actions";
import type { ActionResult } from "@/types/action";
import type { Campaign } from "@/types/campaign";

import { formToCampaignPayload, formToCreatePayload } from "../_lib/campaign-form-payload";
import {
  DEFAULT_OPEN_SECTIONS,
  sectionForField,
  type BuilderSectionId,
} from "../_lib/campaign-form-sections";
import { validateDraft, validatePublish, type FieldErrors } from "../_lib/campaign-form-validation";
import { emptyCampaignForm } from "../_lib/campaign-form-values";
import { campaignToForm } from "../_lib/campaign-to-form";
import { fieldId } from "../_lib/field-id";
import { useCampaignValues, type CampaignValues } from "./use-campaign-values";

export interface UseCampaignFormOptions {
  /** Absent when creating; the form then saves through `POST /campaigns`. */
  campaign?: Campaign;
}

export interface CampaignForm extends CampaignValues {
  pending: boolean;
  dirty: boolean;
  /** A failed submit, summarised above the form for the fields off screen. */
  summary: string | null;
  openSections: string[];
  setOpenSections: (sections: string[]) => void;
  saveDraft: () => void;
  publish: () => void;
}

/**
 * What the builder's two buttons do.
 *
 * Two submit paths with two different contracts: `saveDraft` needs only a name,
 * `publish` runs the full contract. Both mark every unmet field at once, open
 * the sections holding them and move focus to the first - a disabled Publish
 * button that never says why is the failure mode this is written to avoid.
 *
 * The field state itself lives in `useCampaignValues`; this hook composes it.
 */
export function useCampaignForm({ campaign }: UseCampaignFormOptions): CampaignForm {
  const router = useRouter();
  const initial = useMemo(
    () => (campaign ? campaignToForm(campaign) : emptyCampaignForm()),
    [campaign],
  );

  const fields = useCampaignValues(initial);
  // The last state that reached the server. Compared by identity, and set on
  // save rather than derived from `initial`, which is rebuilt on every server
  // refresh and would otherwise report a just-saved form as dirty forever.
  const [saved, setSaved] = useState(initial);
  const [summary, setSummary] = useState<string | null>(null);
  const [openSections, setOpenSections] = useState<string[]>(DEFAULT_OPEN_SECTIONS);
  const [focusField, setFocusField] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const { values, replaceErrors } = fields;

  // Focus runs after the accordion has re-rendered: Radix unmounts collapsed
  // content, so a field inside a section opened in the same tick does not
  // exist yet when the state update commits.
  useEffect(() => {
    if (!focusField) return;

    const timer = setTimeout(() => {
      const element = document.getElementById(fieldId(focusField));
      element?.focus();
      element?.scrollIntoView({ block: "center", behavior: "smooth" });
      setFocusField(null);
    }, 80);

    return () => clearTimeout(timer);
  }, [focusField]);

  /** Surfaces a failure: inline errors, the sections holding them, and focus. */
  function report(fieldErrors: FieldErrors, message: string) {
    replaceErrors(fieldErrors);
    setSummary(message);

    const failed = Object.keys(fieldErrors);
    if (failed.length === 0) return;

    const sections = new Set<BuilderSectionId>(failed.map(sectionForField));
    setOpenSections((current) => [...new Set([...current, ...sections])]);
    setFocusField(failed[0]);
  }

  function handleFailure(result: Extract<ActionResult<unknown>, { ok: false }>) {
    if (Object.keys(result.fieldErrors).length > 0) {
      report(result.fieldErrors, result.message);
    } else {
      setSummary(result.message);
    }
    toast.error(result.message);
  }

  function submit(publishAfter: boolean) {
    const snapshot = values;
    const clientErrors = publishAfter ? validatePublish(snapshot) : validateDraft(snapshot);

    if (Object.keys(clientErrors).length > 0) {
      report(
        clientErrors,
        publishAfter
          ? "This campaign is not ready to publish yet. Fix the fields below."
          : "Some fields need attention before this can be saved.",
      );
      return;
    }

    replaceErrors({});
    setSummary(null);

    startTransition(async () => {
      const result = campaign
        ? await updateCampaignAction(campaign.id, formToCampaignPayload(snapshot))
        : await createCampaignAction(formToCreatePayload(snapshot));

      if (!result.ok) {
        handleFailure(result);
        return;
      }

      setSaved(snapshot);

      if (!publishAfter) {
        if (campaign) {
          toast.success("Draft saved.");
          router.refresh();
        } else {
          // A new campaign has no creative yet, and cannot publish without
          // one, so the next step is the ads screen rather than back to the
          // settings the user has just finished.
          toast.success("Campaign created. Now add an ad.");
          router.replace(`/campaigns/${result.data.id}/ads`);
        }
        return;
      }

      const published = await changeCampaignStatusAction(result.data.id, "ACTIVE");

      // The save already succeeded, so a rejected publish must not strand a
      // new campaign on a URL that no longer matches it.
      if (!campaign) router.replace(`/campaigns/${result.data.id}/ads`);

      if (!published.ok) {
        handleFailure(published);
        return;
      }

      toast.success("Campaign published. Recipients can open it now.");
      router.refresh();
    });
  }

  return {
    ...fields,
    pending,
    dirty: values !== saved,
    summary,
    openSections,
    setOpenSections,
    saveDraft: () => submit(false),
    publish: () => submit(true),
  };
}
