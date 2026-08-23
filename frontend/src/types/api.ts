/**
 * Transport-level types shared by every endpoint.
 *
 * The backend returns one error shape for every failure - validation, HTTP and
 * unexpected alike - so the client never branches on the shape of a failure.
 * See `backend/README.md` ("Error envelope") and
 * `docs/campaign-data-model.md#error-codes`.
 */

/** One field-level problem inside an error envelope. */
export interface ApiErrorDetail {
  /** Dotted path to the offending field, e.g. `ads.0.options.0.label`. */
  field?: string | null;
  code?: string | null;
  message: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  /** Always an array, even for a single problem. */
  details: ApiErrorDetail[];
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}

/** Error codes the UI reacts to specifically; any other string is still valid. */
export type KnownErrorCode =
  | "VALIDATION_ERROR"
  | "CAMPAIGN_NOT_FOUND"
  | "CAMPAIGN_NOT_LIVE"
  | "CAMPAIGN_LOCKED"
  | "CAMPAIGN_INVALID_TRANSITION"
  | "INTERNAL_ERROR";
