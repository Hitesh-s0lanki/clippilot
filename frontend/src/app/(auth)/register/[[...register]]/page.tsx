import { SignUp } from "@clerk/nextjs";
import type { Metadata } from "next";

import { clerkAuthAppearance } from "../../_lib/clerk-appearance";

export const metadata: Metadata = {
  title: "Create an account",
};

/** Catch-all for the same reason as `/login` - Clerk owns the sub-paths. */
export default function RegisterPage() {
  return <SignUp path="/register" appearance={clerkAuthAppearance} />;
}
