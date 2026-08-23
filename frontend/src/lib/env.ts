/**
 * Environment access, resolved once and validated at import time.
 *
 * `NEXT_PUBLIC_*` values are inlined by the bundler, so they must be read as
 * full literal member expressions - destructuring `process.env` breaks the
 * replacement and the value arrives as `undefined` in the browser.
 */

function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(
      `Missing environment variable ${name}. Copy .env.example to .env.local and set it.`,
    );
  }
  return value;
}

function withoutTrailingSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

const publicApiBaseUrl = withoutTrailingSlash(
  required("NEXT_PUBLIC_API_BASE_URL", process.env.NEXT_PUBLIC_API_BASE_URL),
);

/** Server-only override, for when the server reaches the API on another host. */
const serverApiBaseUrl = process.env.API_BASE_URL
  ? withoutTrailingSlash(process.env.API_BASE_URL)
  : publicApiBaseUrl;

/**
 * Where the account screens live.
 *
 * Clerk reads these paths from the environment itself - `auth().redirectToSignIn()`
 * runs on the server and can only see env vars, not props - so they are read back
 * from the same variables here rather than duplicated as literals. One source of
 * truth means an internal `<Link>` and a Clerk redirect can never disagree.
 */
const authRoutes = {
  signIn: process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL || "/login",
  signUp: process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL || "/register",
  /** Landing spot after a sign-in that had no `redirect_url` to return to. */
  afterSignIn: process.env.NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL || "/dashboard",
  afterSignUp: process.env.NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL || "/dashboard",
  /** Not an env var Clerk knows: passed to `<ClerkProvider afterSignOutUrl>`. */
  afterSignOut: "/",
} as const;

export const env = {
  /** Always the browser-reachable origin. */
  apiBaseUrl: publicApiBaseUrl,
  /** Origin to call from Server Components; falls back to `apiBaseUrl`. */
  serverApiBaseUrl,
  /** Business routes live under this prefix; operational ones sit at the root. */
  apiPrefix: "/api/v1",
  /**
   * Clerk's frontend key. Required: without it `<ClerkProvider>` fails deep in
   * the SDK, so it is named here where the message can say what to do.
   */
  clerkPublishableKey: required(
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
  ),
  authRoutes,
  isProduction: process.env.NODE_ENV === "production",
} as const;

/** The origin to use from wherever this code happens to be running. */
export function resolveApiBaseUrl(): string {
  return typeof window === "undefined" ? env.serverApiBaseUrl : env.apiBaseUrl;
}
