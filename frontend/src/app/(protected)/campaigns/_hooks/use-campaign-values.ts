"use client";

import { useCallback, useState } from "react";

import { validateDraft, type FieldErrors } from "../_lib/campaign-form-validation";
import {
  emptyRecipient,
  type CampaignFormValues,
  type OptionFormValues,
  type RecipientFormValues,
} from "../_lib/campaign-form-values";
import { FIELD_PATHS, optionFieldPaths, recipientFieldPaths } from "../_lib/field-paths";

export interface CampaignValues {
  values: CampaignFormValues;
  errors: FieldErrors;
  setField: <K extends keyof CampaignFormValues>(key: K, value: CampaignFormValues[K]) => void;
  setOption: (position: number, patch: Partial<OptionFormValues>) => void;
  setRecipient: (index: number, patch: Partial<RecipientFormValues>) => void;
  addRecipient: () => void;
  removeRecipient: (index: number) => void;
  /** Re-checks every field the user has already touched. Call it on blur. */
  revalidate: () => void;
  /** Replaces the whole error map, e.g. with what a rejected submit returned. */
  replaceErrors: (errors: FieldErrors) => void;
}

/**
 * The builder's field state and its error map.
 *
 * Split out from `use-campaign-form` because these are two jobs: this one owns
 * what is in the fields, that one owns what happens when you press a button.
 *
 * Errors follow the field, not the submit. Editing a field clears its own
 * message immediately and marks it touched; blurring re-checks everything
 * touched so far. Fields nobody has been near stay quiet until a submit asks
 * about them, so opening the builder and tabbing through does not paint the
 * form red.
 */
export function useCampaignValues(initial: CampaignFormValues): CampaignValues {
  const [values, setValues] = useState<CampaignFormValues>(initial);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<ReadonlySet<string>>(new Set());

  /** Marks paths as touched and drops their stale errors in one step. */
  const touch = useCallback((paths: string[]) => {
    setTouched((current) => {
      const next = new Set(current);
      for (const path of paths) next.add(path);
      return next;
    });
    setErrors((current) => {
      if (!paths.some((path) => path in current)) return current;
      const next = { ...current };
      for (const path of paths) delete next[path];
      return next;
    });
  }, []);

  const setField = useCallback(
    <K extends keyof CampaignFormValues>(key: K, value: CampaignFormValues[K]) => {
      touch([FIELD_PATHS[key]]);
      setValues((current) => ({ ...current, [key]: value }));
    },
    [touch],
  );

  const setOption = useCallback(
    (position: number, patch: Partial<OptionFormValues>) => {
      touch(optionFieldPaths(position, patch));
      setValues((current) => ({
        ...current,
        options: current.options.map((option) =>
          option.position === position ? { ...option, ...patch } : option,
        ),
      }));
    },
    [touch],
  );

  const setRecipient = useCallback(
    (index: number, patch: Partial<RecipientFormValues>) => {
      touch(recipientFieldPaths(index, patch));
      setValues((current) => ({
        ...current,
        recipients: current.recipients.map((recipient, position) =>
          position === index ? { ...recipient, ...patch } : recipient,
        ),
      }));
    },
    [touch],
  );

  const addRecipient = useCallback(() => {
    touch(["recipients"]);
    setValues((current) => ({
      ...current,
      audience_type: "LIST",
      recipients: [...current.recipients, emptyRecipient()],
    }));
  }, [touch]);

  const removeRecipient = useCallback(
    (index: number) => {
      touch(["recipients"]);
      setValues((current) => {
        const remaining = current.recipients.filter((_, position) => position !== index);
        return { ...current, recipients: remaining.length ? remaining : [emptyRecipient()] };
      });
    },
    [touch],
  );

  const revalidate = useCallback(() => {
    const fresh = validateDraft(values);
    setErrors((current) => {
      const next = { ...current };
      for (const [field, message] of Object.entries(fresh)) {
        if (touched.has(field)) next[field] = message;
      }
      return next;
    });
  }, [values, touched]);

  const replaceErrors = useCallback((next: FieldErrors) => {
    setErrors(next);
    setTouched((current) => new Set([...current, ...Object.keys(next)]));
  }, []);

  return {
    values,
    errors,
    setField,
    setOption,
    setRecipient,
    addRecipient,
    removeRecipient,
    revalidate,
    replaceErrors,
  };
}
