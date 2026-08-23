import { AuthBrandPanel } from "./_components/auth-brand-panel";
import { AuthFormPanel } from "./_components/auth-form-panel";

/**
 * Shell for the account routes: a two-sided screen, split down the middle.
 *
 * Equal halves - `grid-cols-2` - engaging at `lg`, where half a viewport is
 * still wider than the 25rem card Clerk sizes itself to. Below that the brand
 * panel steps aside rather than shrinking into an unreadable strip, and the
 * form takes the single column.
 *
 * `h-dvh` with `overflow-hidden` caps the screen at the viewport: an account
 * screen is one card and a paragraph, and a page that scrolls to reveal more of
 * either is a sign the panel is carrying too much. Each half scrolls
 * internally instead, so a short laptop or a tall sign-up form is still
 * reachable without the page itself moving.
 *
 * No app chrome: the root layout renders none, and a site header offering
 * "Sign in" on top of the sign-in page is exactly the duplication this layout
 * avoids. Clerk's `<SignIn>` and `<SignUp>` bring their own card, so the form
 * column adds spacing and nothing that would double the border.
 */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="grid h-dvh overflow-hidden lg:grid-cols-2">
      <AuthBrandPanel />
      <AuthFormPanel>{children}</AuthFormPanel>
    </div>
  );
}
