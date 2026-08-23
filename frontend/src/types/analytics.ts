/**
 * Analytics types for `GET /campaigns/{id}/analytics`.
 *
 * Two rules the backend guarantees, which the UI is built on:
 * `interaction_rate` is `0` when `views` is `0`, and `by_option` carries a row
 * for every option including zero-click ones - so a chart never has to guess
 * at a missing bar.
 */

import type { CampaignObjective, OptionIntent, PrimaryMetric } from "./campaign";

export interface OptionBreakdown {
  option_id: string;
  position: number;
  key: string;
  label: string;
  intent: OptionIntent;
  clicks: number;
  /** Fraction of interactions, `0.0-1.0`. Sums to 1, or 0 when there are none. */
  share: number;
}

export interface TimeseriesPoint {
  /** `YYYY-MM-DD`. */
  date: string;
  views: number;
  interactions: number;
}

export interface CampaignAnalytics {
  campaign_id: string;
  objective: CampaignObjective;

  views: number;
  interactions: number;
  interaction_rate: number;
  unique_viewers: number;

  by_option: OptionBreakdown[];
  primary_metric: PrimaryMetric | null;

  first_activity_at: string | null;
  last_activity_at: string | null;
  timeseries: TimeseriesPoint[];
}
