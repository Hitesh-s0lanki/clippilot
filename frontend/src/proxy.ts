import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

/**
 * Clerk request proxy.
 *
 * Next.js 16 renamed Middleware to Proxy; the file must sit beside `app/`,
 * which is why it lives in `src/` rather than the project root. See
 * `node_modules/next/dist/docs/01-app/01-getting-started/16-proxy.md`.
 */

/**
 * Everything a recipient touches, the public ads library, plus the account
 * routes themselves.
 *
 * Listed as an allowlist rather than protecting named prefixes, so a new
 * screen is private by the fact that nobody added it here - a forgotten
 * campaign route leaks nothing.
 */
const isPublicRoute = createRouteMatcher([
  "/",
  "/ads(.*)",
  "/login(.*)",
  "/register(.*)",
  "/preview(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  if (isPublicRoute(request)) return;

  // Redirects documents to NEXT_PUBLIC_CLERK_SIGN_IN_URL and answers 404 for
  // data requests, so a signed-out fetch never renders half a screen.
  await auth.protect();
});

export const config = {
  // Skip Next internals and static files, run on everything else. Route
  // handlers are matched explicitly because they can be hit without a
  // document request.
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
