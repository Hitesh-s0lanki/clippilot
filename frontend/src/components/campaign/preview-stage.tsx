"use client";

import { useRef, useState } from "react";

import { isApiError } from "@/lib/api/errors";
import { recordResponse, recordView } from "@/lib/api/public";
import { getPreviewSessionId } from "@/lib/preview-session";
import type { CampaignPreview, FollowUp, PreviewOption } from "@/types/preview";

import { PreviewDisclaimer } from "./preview-disclaimer";
import { PreviewFollowUp } from "./preview-follow-up";
import { PreviewMessage } from "./preview-message";
import { PreviewOptions } from "./preview-options";
import { PreviewPlayer } from "./preview-player";

export type PreviewMode = "live" | "owner";

export interface PreviewStageProps {
  preview: CampaignPreview;
  /** `owner` resolves the follow-up locally and records nothing. */
  mode?: PreviewMode;
  /** Option id -> follow-up, supplied by the owner's dry run. */
  followUps?: Record<string, FollowUp>;
}

/**
 * The interactive part of the preview.
 *
 * Two modes, one screen. `live` records through the public API, which is
 * idempotent per session, so a double-click returns the original event and the
 * follow-up for the option first chosen rather than switching the outcome.
 * `owner` renders exactly the same thing from data the builder already has and
 * writes nothing, so checking a draft cannot pollute its own analytics.
 *
 * A view is recorded when playback starts, and again - harmlessly, because the
 * call is idempotent - before a response, so the interaction rate can never
 * exceed 1 for a recipient who answered without pressing play.
 */
export function PreviewStage({ preview, mode = "live", followUps = {} }: PreviewStageProps) {
  const viewed = useRef(false);

  const [chosen, setChosen] = useState<PreviewOption | null>(null);
  const [followUp, setFollowUp] = useState<FollowUp | null>(null);
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { ad, compliance } = preview;

  async function markViewed() {
    if (mode !== "live" || viewed.current) return;
    viewed.current = true;

    try {
      await recordView({
        campaignId: preview.campaign_id,
        sessionId: getPreviewSessionId(preview.campaign_id),
        adId: ad.id,
        memberId: preview.member_id,
      });
    } catch {
      // A missed view must not stop the recipient from answering.
      viewed.current = false;
    }
  }

  async function choose(option: PreviewOption) {
    if (submittingId || followUp) return;

    setError(null);
    setSubmittingId(option.id);

    if (mode === "owner") {
      setChosen(option);
      setFollowUp(
        followUps[option.id] ?? {
          follow_up_type: "MESSAGE",
          follow_up_message: "No follow-up configured for this option yet.",
          follow_up_url: null,
        },
      );
      setSubmittingId(null);
      return;
    }

    try {
      await markViewed();
      const result = await recordResponse({
        campaignId: preview.campaign_id,
        sessionId: getPreviewSessionId(preview.campaign_id),
        optionId: option.id,
        adId: ad.id,
        memberId: preview.member_id,
      });

      setChosen(option);
      setFollowUp(result);
    } catch (caught) {
      setError(
        isApiError(caught)
          ? caught.message
          : "Your response could not be recorded. Check your connection and try again.",
      );
    } finally {
      setSubmittingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <PreviewPlayer
        videoUrl={ad.video_url}
        posterUrl={ad.poster_url}
        captionsUrl={ad.captions_url}
        title={`${preview.campaign_name} video`}
        onPlay={markViewed}
      />

      <PreviewMessage
        headline={ad.headline}
        description={ad.description}
        message={ad.personalised_message}
      />

      {followUp && chosen ? (
        <PreviewFollowUp followUp={followUp} chosenLabel={chosen.label} />
      ) : (
        <PreviewOptions
          options={ad.options}
          submittingId={submittingId}
          disabled={Boolean(submittingId)}
          onChoose={choose}
        />
      )}

      {error ? (
        <p role="alert" className="text-center text-sm font-medium text-destructive">
          {error}
        </p>
      ) : null}

      {compliance.disclaimer_text ? <PreviewDisclaimer text={compliance.disclaimer_text} /> : null}
    </div>
  );
}
