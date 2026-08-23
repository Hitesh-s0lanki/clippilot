"use client";

import { SparklesIcon, TriangleAlertIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import { resolveVariables } from "../_lib/personalisation";
import { BuilderField } from "./builder-field";

export interface BuilderMessageFieldProps {
  value: string;
  error?: string;
  /**
   * A name to render the live preview against.
   *
   * Optional: the ad form does not know who is in the audience, so with no
   * name the preview shows the same neutral fallback a member with no name
   * would see, which is the honest thing to show.
   */
  customerName?: string;
  /** Resolves {{campaign_name}} in the preview. */
  campaignName: string;
  onChange: (value: string) => void;
  onBlur: () => void;
}

const VARIABLE = "{{customer_name}}";

/**
 * The personalised message, with its resolution shown live.
 *
 * The variable is the one piece of syntax the brief puts in front of a user,
 * and a template language nobody can see the output of is a template language
 * people get wrong. The preview underneath resolves it using the same rules
 * the server will - including the fallback to "there" when nobody is named,
 * and leaving an unknown variable literal rather than silently blanking it.
 */
export function BuilderMessageField({
  value,
  error,
  customerName = "",
  campaignName,
  onChange,
  onBlur,
}: BuilderMessageFieldProps) {
  const resolved = resolveVariables(value, { customerName, campaignName });

  return (
    <BuilderField
      field="ads.0.personalised_message"
      label="Personalised message"
      required
      error={error}
      hint={`Supports ${VARIABLE}, which is replaced with each recipient's name.`}
    >
      {(control) => (
        <div className="space-y-2">
          <Textarea
            {...control}
            rows={3}
            maxLength={500}
            value={value}
            placeholder={`Hi ${VARIABLE}, we have something selected for you.`}
            onChange={(event) => onChange(event.target.value)}
            onBlur={onBlur}
          />

          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="xs"
              onClick={() =>
                onChange(`${value}${value.endsWith(" ") || !value ? "" : " "}${VARIABLE}`)
              }
            >
              <SparklesIcon data-icon="inline-start" />
              Insert {VARIABLE}
            </Button>
            <span className="text-xs text-muted-foreground tabular-nums">{value.length}/500</span>
          </div>

          <div className="rounded-lg border border-dashed border-border bg-muted/40 px-3 py-2">
            <p className="text-xs font-medium text-muted-foreground">
              Preview for {customerName.trim() || "someone in this audience"}
            </p>
            <p className="mt-1 leading-relaxed text-pretty">
              {resolved.text || <span className="text-muted-foreground">Nothing to show yet.</span>}
            </p>
          </div>

          {resolved.unresolved.length > 0 ? (
            <p role="alert" className="flex items-start gap-1.5 text-xs text-warning">
              <TriangleAlertIcon aria-hidden className="mt-px size-3.5 shrink-0" />
              <span>
                {resolved.unresolved.map((name) => `{{${name}}}`).join(", ")} is not a known
                variable and will be shown to the recipient exactly as written.
              </span>
            </p>
          ) : null}
        </div>
      )}
    </BuilderField>
  );
}
