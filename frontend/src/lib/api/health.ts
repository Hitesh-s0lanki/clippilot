import { api } from "./client";
import { isApiError } from "./errors";

/** Shape of `GET /healthz` - see `backend/README.md`. */
export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  timestamp: string;
}

/**
 * Probes the API.
 *
 * `/healthz` is an operational route, so it sits at the root rather than under
 * the version prefix - hence `versioned: false`. Kept on a short timeout: this
 * runs on the home page and a hung backend should read as "down", not as a
 * page that never renders.
 */
export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return api.get<HealthResponse>("/healthz", {
    versioned: false,
    timeoutMs: 4_000,
    cache: "no-store",
    signal,
  });
}

/** What the landing page needs to know: it reached the API, or why it did not. */
export type HealthProbe =
  { reachable: true; health: HealthResponse } | { reachable: false; message: string };

/**
 * `getHealth` with the failure caught.
 *
 * An unreachable API is an expected state on a public page - the backend may
 * simply not be running yet - so it resolves to data rather than throwing at
 * the route's error boundary. The `try` wraps only the request; anything built
 * from the result belongs outside it.
 */
export async function probeHealth(): Promise<HealthProbe> {
  try {
    return { reachable: true, health: await getHealth() };
  } catch (error) {
    return {
      reachable: false,
      message: isApiError(error) ? error.message : "Could not reach the ClipPilot API.",
    };
  }
}
