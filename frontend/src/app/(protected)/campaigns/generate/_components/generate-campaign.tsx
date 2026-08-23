"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { createFromDraftAction, draftCampaignAction } from "@/lib/actions/agent-actions";
import type { CampaignStrategyResponse } from "@/types/agent";
import type { AudienceSummary } from "@/types/audience";

import { strategyToPayload } from "../_lib/strategy-to-payload";
import { GenerateBriefForm } from "./generate-brief-form";
import { GeneratePending } from "./generate-pending";
import { StrategyAccept } from "./strategy-accept";
import { StrategyAnalysis } from "./strategy-analysis";
import { StrategyCaveats } from "./strategy-caveats";
import { StrategyDraftSummary } from "./strategy-draft-summary";

export interface GenerateCampaignProps {
  audiences: AudienceSummary[];
}

/**
 * Brief in, campaign out - with a read of the draft in between.
 *
 * Three states and one rule: **nothing is written until the draft is
 * accepted.** Generating is slow and costs money upstream; creating is instant
 * and irreversible, so they are two decisions rather than one button. A draft
 * the user does not like costs them the run and nothing else.
 */
export function GenerateCampaign({ audiences }: GenerateCampaignProps) {
  const router = useRouter();
  const [brief, setBrief] = useState("");
  const [result, setResult] = useState<CampaignStrategyResponse | null>(null);
  const [audienceId, setAudienceId] = useState(audiences[0]?.id ?? "");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function generate() {
    setError(null);

    startTransition(async () => {
      // Just the sentence. The agent reads the business, the market and the
      // competitors out of it, or researches them.
      const outcome = await draftCampaignAction({ requirements: brief.trim() });

      if (!outcome.ok) {
        setError(outcome.fieldErrors.requirements ?? outcome.message);
        toast.error(outcome.message);
        return;
      }

      setResult(outcome.data);
    });
  }

  function accept() {
    if (!result) return;

    startTransition(async () => {
      const outcome = await createFromDraftAction(strategyToPayload(result.strategy, audienceId));

      if (!outcome.ok) {
        toast.error(outcome.message);
        return;
      }

      // Straight to the ads: every generated ad still needs its video, and
      // that is the next real piece of work.
      toast.success("Campaign created. Add a video to each ad to finish it.");
      router.push(`/campaigns/${outcome.data.id}/ads`);
    });
  }

  if (pending && !result) return <GeneratePending />;

  if (!result) {
    return (
      <GenerateBriefForm
        value={brief}
        error={error}
        pending={pending}
        onChange={setBrief}
        onSubmit={generate}
      />
    );
  }

  return (
    <div className="space-y-4">
      <StrategyCaveats strategy={result.strategy} meta={result.meta} />
      <StrategyAnalysis strategy={result.strategy} />
      <StrategyDraftSummary draft={result.strategy.campaign} />

      <StrategyAccept
        audiences={audiences}
        audienceId={audienceId}
        pending={pending}
        onAudienceChange={setAudienceId}
        onAccept={accept}
        onDiscard={() => {
          setResult(null);
          setError(null);
        }}
      />
    </div>
  );
}
