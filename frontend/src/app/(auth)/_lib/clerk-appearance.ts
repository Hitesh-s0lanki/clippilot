/**
 * Appearance shared by `<SignIn>` and `<SignUp>`.
 *
 * The split leaves the card a quarter of the viewport - 256px of it at the
 * 1280px breakpoint where the two-sided layout starts. Both `auto` and
 * `blockButton` put the provider name beside the icon and lay two providers
 * out side by side, which at that width truncates them to "Go..." and
 * "Lin...". Icon buttons carry the provider in an accessible name instead of
 * a visible label that can be clipped, so they read the same at every column
 * width, and on a phone Clerk widens them into full-row tap targets.
 */
export const clerkAuthAppearance = {
  options: {
    socialButtonsVariant: "iconButton",
  },
} as const;
