import type { ApiErrorDetail, ApiErrorEnvelope } from "@/types/api";

/**
 * A failed API call, carrying the backend's error envelope intact so callers
 * can map `details` onto form fields without re-parsing the response.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];

  constructor(status: number, code: string, message: string, details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** `true` when the request never reached the server (offline, DNS, timeout). */
  get isNetworkError(): boolean {
    return this.status === 0;
  }

  /** Field path -> first message, ready to hand to a form. */
  fieldErrors(): Record<string, string> {
    const errors: Record<string, string> = {};
    for (const detail of this.details) {
      if (detail.field && !(detail.field in errors)) {
        errors[detail.field] = detail.message;
      }
    }
    return errors;
  }
}

/** Narrows an unknown thrown value, since `catch` bindings are `unknown`. */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

function isErrorEnvelope(body: unknown): body is ApiErrorEnvelope {
  if (typeof body !== "object" || body === null || !("error" in body)) return false;
  const { error } = body as { error: unknown };
  return typeof error === "object" && error !== null && "code" in error && "message" in error;
}

/**
 * Builds an `ApiError` from a failed response, tolerating bodies that are not
 * the envelope at all - a proxy 502 returns HTML, and that must not surface as
 * a JSON parse error.
 */
export async function apiErrorFromResponse(response: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }

  if (isErrorEnvelope(body)) {
    const { code, message, details } = body.error;
    return new ApiError(response.status, code, message, Array.isArray(details) ? details : []);
  }

  return new ApiError(
    response.status,
    "UNEXPECTED_RESPONSE",
    `Request failed with status ${response.status}.`,
  );
}
