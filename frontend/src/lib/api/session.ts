import "server-only";

import { auth } from "@clerk/nextjs/server";

/**
 * The bridge between Clerk and the FastAPI backend.
 *
 * Clerk owns the session; the backend never sees a credential, only the JWT
 * Clerk minted for it (`backend/src/core/security.py` verifies the signature
 * against Clerk's JWKS and reads `sub` into `campaigns.owner_user_id`). This
 * module is the one place that moves the token from the former to the latter.
 *
 * Server-only on purpose: `auth()` reads request headers, so a client bundle
 * that imported this would either fail to build or silently send nothing.
 */

/**
 * The current Clerk session token, or `null` when nobody is signed in.
 *
 * Call it per request. Holding the result in a module-level variable would
 * leak one session into the next request on the same server process.
 */
export async function getSessionToken(): Promise<string | null> {
  const { getToken } = await auth();
  return getToken();
}
