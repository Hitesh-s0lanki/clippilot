import type { CallToAction, CampaignAd, FollowUpType, OptionIntent } from "@/types/campaign";

/**
 * One ad's form state.
 *
 * Split from the campaign's the moment ads became a 1:N child. A campaign is
 * configured once; its creatives are added one at a time on their own screen,
 * and a single form carrying both meant scrolling past a dozen campaign
 * settings to reach the video.
 *
 * Every field is a string, including the numeric ones - a form input's value is
 * a string whether or not the field is a number, and mirroring that honestly
 * means "" is simply empty rather than `NaN`, `0` or `null` pretending to be.
 */

export interface AdOptionFormValues {
  /** 1 or 2 - the brief's two response options, fixed. */
  position: number;
  label: string;
  intent: OptionIntent;
  follow_up_type: FollowUpType;
  follow_up_message: string;
  follow_up_url: string;
}

export interface AdFormValues {
  name: string;
  video_url: string;
  poster_url: string;
  headline: string;
  description: string;
  cta: CallToAction;
  personalised_message: string;
  options: AdOptionFormValues[];
}

export const DEFAULT_MESSAGE = "Hi {{customer_name}}, we have something selected for you.";

function emptyOption(position: number, intent: OptionIntent): AdOptionFormValues {
  return {
    position,
    label: "",
    intent,
    follow_up_type: "MESSAGE",
    follow_up_message: "",
    follow_up_url: "",
  };
}

/** A new ad, pre-filled with the defaults the API would apply anyway. */
export function emptyAdForm(): AdFormValues {
  return {
    name: "",
    video_url: "",
    poster_url: "",
    headline: "",
    description: "",
    cta: "LEARN_MORE",
    personalised_message: DEFAULT_MESSAGE,
    options: [emptyOption(1, "POSITIVE"), emptyOption(2, "NEGATIVE")],
  };
}

/**
 * An existing ad, flattened into form state.
 *
 * Built on top of a blank form rather than field by field, so an ad saved
 * before a field existed lands on the same defaults a new one would rather
 * than on `undefined`.
 */
export function adToForm(ad: CampaignAd): AdFormValues {
  const blank = emptyAdForm();

  return {
    ...blank,
    name: ad.name,
    video_url: ad.video_url ?? "",
    poster_url: ad.poster_url ?? "",
    headline: ad.headline ?? "",
    description: ad.description ?? "",
    cta: ad.cta,
    personalised_message: ad.personalised_message ?? "",
    options: blank.options.map((fallback) => {
      const saved = ad.options.find((option) => option.position === fallback.position);
      if (!saved) return fallback;

      return {
        position: saved.position,
        label: saved.label,
        intent: saved.intent,
        follow_up_type: saved.follow_up_type,
        follow_up_message: saved.follow_up_message ?? "",
        follow_up_url: saved.follow_up_url ?? "",
      };
    }),
  };
}
