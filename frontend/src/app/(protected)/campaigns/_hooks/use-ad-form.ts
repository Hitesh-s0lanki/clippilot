"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState, useTransition } from "react";
import { toast } from "sonner";

import { createAdAction, updateAdAction } from "@/lib/actions/ad-actions";
import type { ActionResult } from "@/types/action";
import type { CampaignAd } from "@/types/campaign";

import { adFormToPayload } from "../_lib/ad-form-payload";
import { validateAdDraft } from "../_lib/ad-form-validation";
import {
  adToForm,
  emptyAdForm,
  type AdFormValues,
  type AdOptionFormValues,
} from "../_lib/ad-form-values";
import type { FieldErrors } from "../_lib/campaign-form-validation";
import { fieldId } from "../_lib/field-id";

export interface UseAdFormOptions {
  campaignId: string;
  /** Absent when creating; the form then saves through `POST .../ads`. */
  ad?: CampaignAd;
}

export interface AdForm {
  values: AdFormValues;
  errors: FieldErrors;
  pending: boolean;
  dirty: boolean;
  /** A failed submit, summarised above the form for the fields off screen. */
  summary: string | null;
  setField: <K extends keyof AdFormValues>(key: K, value: AdFormValues[K]) => void;
  setOption: (position: number, patch: Partial<AdOptionFormValues>) => void;
  /** Re-checks every field the user has already touched. Call it on blur. */
  revalidate: () => void;
  save: () => void;
}

/**
 * One ad's field state and what its Save button does.
 *
 * Errors follow the field, not the submit: editing a field clears its own
 * message and marks it touched, and blurring re-checks everything touched so
 * far. Fields nobody has been near stay quiet until a submit asks about them,
 * so opening the form and tabbing through does not paint it red.
 *
 * Saving only ever needs a name. Whether the ad is *complete* is a separate
 * question, answered when it is switched on - so a half-built creative can be
 * kept without arguing with the form.
 */
export function useAdForm({ campaignId, ad }: UseAdFormOptions): AdForm {
  const router = useRouter();
  const initial = useMemo(() => (ad ? adToForm(ad) : emptyAdForm()), [ad]);

  const [values, setValues] = useState<AdFormValues>(initial);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<ReadonlySet<string>>(new Set());
  const [saved, setSaved] = useState(initial);
  const [summary, setSummary] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  /** Marks paths as touched and drops their stale errors in one step. */
  const touch = useCallback((paths: string[]) => {
    setTouched((current) => new Set([...current, ...paths]));
    setErrors((current) => {
      if (!paths.some((path) => path in current)) return current;
      const next = { ...current };
      for (const path of paths) delete next[path];
      return next;
    });
  }, []);

  const setField = useCallback(
    <K extends keyof AdFormValues>(key: K, value: AdFormValues[K]) => {
      touch([key]);
      setValues((current) => ({ ...current, [key]: value }));
    },
    [touch],
  );

  const setOption = useCallback(
    (position: number, patch: Partial<AdOptionFormValues>) => {
      touch(Object.keys(patch).map((key) => `options.${position}.${key}`));
      setValues((current) => ({
        ...current,
        options: current.options.map((option) =>
          option.position === position ? { ...option, ...patch } : option,
        ),
      }));
    },
    [touch],
  );

  const revalidate = useCallback(() => {
    const fresh = validateAdDraft(values);
    setErrors((current) => {
      const next = { ...current };
      for (const [field, message] of Object.entries(fresh)) {
        if (touched.has(field)) next[field] = message;
      }
      return next;
    });
  }, [values, touched]);

  function report(fieldErrors: FieldErrors, message: string) {
    setErrors(fieldErrors);
    setTouched((current) => new Set([...current, ...Object.keys(fieldErrors)]));
    setSummary(message);

    const first = Object.keys(fieldErrors)[0];
    if (!first) return;

    const element = document.getElementById(fieldId(first));
    element?.focus();
    element?.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  function handleFailure(result: Extract<ActionResult<unknown>, { ok: false }>) {
    if (Object.keys(result.fieldErrors).length > 0) {
      report(result.fieldErrors, result.message);
    } else {
      setSummary(result.message);
    }
    toast.error(result.message);
  }

  function save() {
    const snapshot = values;
    const clientErrors = validateAdDraft(snapshot);

    if (Object.keys(clientErrors).length > 0) {
      report(clientErrors, "Some fields need attention before this can be saved.");
      return;
    }

    setErrors({});
    setSummary(null);

    startTransition(async () => {
      const payload = adFormToPayload(snapshot);
      const result = ad
        ? await updateAdAction(campaignId, ad.id, payload)
        : await createAdAction(campaignId, payload);

      if (!result.ok) {
        handleFailure(result);
        return;
      }

      setSaved(snapshot);
      toast.success(ad ? "Ad saved." : "Ad added.");
      // Back to the list either way: it is where the ad's status lives, and
      // where the next one is added from.
      router.push(`/campaigns/${campaignId}/ads`);
      router.refresh();
    });
  }

  return {
    values,
    errors,
    pending,
    dirty: values !== saved,
    summary,
    setField,
    setOption,
    revalidate,
    save,
  };
}
