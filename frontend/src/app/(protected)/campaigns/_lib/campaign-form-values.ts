import type { BudgetType, CampaignObjective, Pacing, SpecialCategory } from "@/types/campaign";

/**
 * The campaign form's state.
 *
 * Campaign settings only: the creative lives in `ad-form-values.ts`, because
 * ads are a separate screen and a 1:N child.
 *
 * Every field is a string, including the numeric ones. A form input's value is
 * a string whether or not the field is a number, and mirroring that honestly
 * means "" is simply empty rather than `NaN`, `0` or `null` pretending to be
 * empty. The conversion to the wire format happens once, in
 * `campaign-form-payload.ts`.
 */

export interface CampaignFormValues {
  name: string;
  description: string;
  objective: CampaignObjective;

  start_at: string;
  end_at: string;
  timezone: string;

  /**
   * The list this campaign targets, by id. Empty until one is chosen.
   *
   * An audience is account-level and built on its own screen, so the builder
   * selects one rather than carrying rows of people: the same list can be
   * targeted by several campaigns, and editing it here would edit it for all
   * of them.
   */
  audience_id: string;

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

/** A new campaign, pre-filled with the defaults the API would apply anyway. */
export function emptyCampaignForm(timezone = "UTC"): CampaignFormValues {
  return {
    name: "",
    description: "",
    objective: "ENGAGEMENT",

    start_at: "",
    end_at: "",
    timezone,

    audience_id: "",

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
