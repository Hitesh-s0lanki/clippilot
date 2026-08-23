import { env, resolveApiBaseUrl } from "@/lib/env";

import { ApiError, apiErrorFromResponse } from "./errors";

const DEFAULT_TIMEOUT_MS = 10_000;

export type QueryParams = Record<string, string | number | boolean | undefined | null>;

export interface RequestOptions extends Omit<RequestInit, "body" | "method"> {
  /** Serialised as JSON; set `Content-Type` yourself for anything else. */
  body?: unknown;
  /** Appended to the path, skipping `undefined` and `null` values. */
  query?: QueryParams;
  /** Abort after this many milliseconds. Defaults to 10s. */
  timeoutMs?: number;
  /** Prefix the path with `API_PREFIX`. Defaults to `true`. */
  versioned?: boolean;
  /**
   * Clerk session JWT, sent as `Authorization: Bearer`.
   *
   * Passed in by the caller rather than read from a module-level global: on
   * the server one token belongs to one request, and a cached one would hand
   * a session to whoever asked next. `null` is accepted and simply omits the
   * header, so a signed-out call reaches the backend and gets its 401 rather
   * than failing here.
   */
  token?: string | null;
}

function buildUrl(path: string, query: QueryParams = {}, versioned = true): string {
  const prefix = versioned ? env.apiPrefix : "";
  const url = new URL(`${prefix}${path}`, `${resolveApiBaseUrl()}/`);

  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

function toApiError(cause: unknown): ApiError {
  if (cause instanceof DOMException && cause.name === "TimeoutError") {
    return new ApiError(0, "REQUEST_TIMEOUT", "The server took too long to respond.");
  }
  if (cause instanceof DOMException && cause.name === "AbortError") {
    return new ApiError(0, "REQUEST_ABORTED", "The request was cancelled.");
  }
  return new ApiError(0, "NETWORK_ERROR", "Could not reach the ClipPilot API.");
}

async function request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  const {
    body,
    query,
    versioned,
    token,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    headers,
    signal,
    ...init
  } = options;

  const hasBody = body !== undefined;
  const timeout = AbortSignal.timeout(timeoutMs);

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query, versioned), {
      ...init,
      method,
      headers: {
        Accept: "application/json",
        ...(hasBody ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: hasBody ? JSON.stringify(body) : undefined,
      // Compose the caller's signal with the timeout instead of dropping either.
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
  } catch (cause) {
    throw toApiError(cause);
  }

  if (!response.ok) {
    throw await apiErrorFromResponse(response);
  }

  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/**
 * Thin typed wrapper over `fetch`.
 *
 * Every method resolves with the parsed body or throws an {@link ApiError} -
 * there is no `{ data, error }` tuple to unpack, so callers use try/catch and
 * React error boundaries the way they already do for everything else.
 */
export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T>(path: string, options?: RequestOptions) => request<T>("POST", path, options),
  patch: <T>(path: string, options?: RequestOptions) => request<T>("PATCH", path, options),
  put: <T>(path: string, options?: RequestOptions) => request<T>("PUT", path, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
};
