import { SignIn } from "@clerk/nextjs";
import type { Metadata } from "next";

import { clerkAuthAppearance } from "../../_lib/clerk-appearance";

export const metadata: Metadata = {
  title: "Sign in",
};

/**
 * Optional catch-all: Clerk drives its multi-step flows - a second factor,
 * an email link, a password reset - as sub-paths of this one, so the segment
 * has to swallow `/login/factor-one` and friends.
 *
 * Everything else about the flow (where the "Sign up" link points, where a
 * successful sign-in lands) comes from the `NEXT_PUBLIC_CLERK_*` variables,
 * which the server-side helpers read too.
 *
 * The card is the whole page: its own header names the step, and the product
 * context sits in the brand panel beside it, so there is nothing to add above.
 */
export default function LoginPage() {
  return <SignIn path="/login" appearance={clerkAuthAppearance} />;
}
