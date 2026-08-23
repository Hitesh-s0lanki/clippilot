import { AuthBrandPanel } from "./_components/auth-brand-panel";
import { AuthFormPanel } from "./_components/auth-form-panel";

/**
 * Shell for the account routes: a two-sided screen, brand panel to form column
 * at 3:1.
 *
 * The ratio is exact - `3fr 1fr` - and engages at `xl`. Below that a quarter of
 * the viewport is narrower than a sign-in card can usefully be, so the grid
 * drops to the single column the panel is already hidden at.
 *
 * No app chrome: the root layout renders none, and a site header offering
 * "Sign in" on top of the sign-in page is exactly the duplication this layout
 * avoids. Clerk's `<SignIn>` and `<SignUp>` bring their own card, so the form
 * column adds spacing and nothing that would double the border.
 */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="grid min-h-dvh flex-1 xl:grid-cols-[3fr_1fr]">
      <AuthBrandPanel />
      <AuthFormPanel>{children}</AuthFormPanel>
    </div>
  );
}
