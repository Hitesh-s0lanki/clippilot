import type {
  AudienceType,
  BudgetType,
  CampaignObjective,
  FollowUpType,
  OptionIntent,
  Pacing,
  SpecialCategory,
} from "@/types/campaign";

/**
 * The builder's form state.
 *
 * Every field is a string, including the numeric ones. A form input's value is
 * a string whether or not the field is a number, and mirroring that honestly
 * means "" is simply empty rather than `NaN`, `0` or `null` pretending to be
 * empty. The conversion to the wire format happens once, in
 * `campaign-form-payload.ts`.
 */

export interface OptionFormValues {
  /** 1 or 2 - the brief's two response options, fixed. */
  position: number;
  label: string;
  intent: OptionIntent;
  follow_up_type: FollowUpType;
  follow_up_message: string;
  follow_up_url: string;
}

export interface RecipientFormValues {
  customer_name: string;
  email: string;
  phone: string;
  external_ref: string;
}

export interface CampaignFormValues {
  name: string;
  description: string;
  objective: CampaignObjective;

  start_at: string;
  end_at: string;
  timezone: string;

  audience_type: AudienceType;
  recipients: RecipientFormValues[];

  video_url: string;
  poster_url: string;
  headline: string;
  personalised_message: string;
  options: OptionFormValues[];

  special_category: SpecialCategory;
  disclaimer_text: string;

  budget_type: BudgetType;
  /** Major units as typed, e.g. `50000`. Converted to minor units on save. */
  budget_amount: string;
  currency: string;
  spend_cap: string;
  pacing: Pacing;
  send_cap_total: string;
  send_cap_per_day: string;
  frequency_cap_per_recipient: string;

  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  utm_content: string;
  external_ref: string;
}

export const DEFAULT_MESSAGE = "Hi {{customer_name}}, we have something selected for you.";

function emptyOption(position: number, intent: OptionIntent): OptionFormValues {
  return {
    position,
    label: "",
    intent,
    follow_up_type: "MESSAGE",
    follow_up_message: "",
    follow_up_url: "",
  };
}

export function emptyRecipient(): RecipientFormValues {
  return { customer_name: "", email: "", phone: "", external_ref: "" };
}

/** A new campaign, pre-filled with the defaults the API would apply anyway. */
export function emptyCampaignForm(timezone = "UTC"): CampaignFormValues {
  return {
    name: "",
    description: "",
    objective: "ENGAGEMENT",

    start_at: "",
    end_at: "",
    timezone,

    audience_type: "SINGLE",
    recipients: [emptyRecipient()],

    video_url: "",
    poster_url: "",
    headline: "",
    personalised_message: DEFAULT_MESSAGE,
    options: [emptyOption(1, "POSITIVE"), emptyOption(2, "NEGATIVE")],

    special_category: "NONE",
    disclaimer_text: "",

    budget_type: "NONE",
    budget_amount: "",
    currency: "INR",
    spend_cap: "",
    pacing: "STANDARD",
    send_cap_total: "",
    send_cap_per_day: "",
    frequency_cap_per_recipient: "1",

    utm_source: "trustvid",
    utm_medium: "interactive-video",
    utm_campaign: "",
    utm_content: "",
    external_ref: "",
  };
}
