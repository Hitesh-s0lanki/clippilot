import { auth } from "@clerk/nextjs/server";
import { cookies } from "next/headers";

import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";

import { AppSidebar } from "./_components/app-sidebar";
import { AppTopbar } from "./_components/app-topbar";

/** shadcn's sidebar writes its expanded/collapsed state under this name. */
const SIDEBAR_COOKIE = "sidebar_state";

/**
 * The session guard and the app shell for every route in this group.
 *
 * `src/proxy.ts` already turns anonymous requests away, so `auth.protect()` is
 * the second lock rather than the first: it keeps the guarantee attached to the
 * route tree, so a change to the proxy's matcher cannot quietly expose a
 * screen. It redirects to the sign-in page for documents and answers 404 for
 * data requests, which is also what the backend does for a campaign owned by
 * someone else.
 *
 * The chrome here is the sidebar rail, not the marketing header the public
 * pages render. Reading the sidebar cookie on the server is what stops a
 * collapsed rail from flashing open on every navigation: `SidebarProvider`
 * would otherwise start from its own default and only learn the real state
 * after hydration.
 *
 * `SidebarInset` renders the page's `<main>` landmark, so nothing inside this
 * group renders another one.
 *
 * `TooltipProvider` is required, not decorative: a `SidebarMenuButton` given a
 * `tooltip` renders a Radix tooltip, which throws outright without a provider
 * above it. It sits at the shell rather than around the rail so any tooltip a
 * console screen adds later is already covered.
 */
export default async function ProtectedLayout({ children }: LayoutProps<"/">) {
  await auth.protect();

  const store = await cookies();
  const defaultOpen = store.get(SIDEBAR_COOKIE)?.value !== "false";

  return (
    <TooltipProvider>
      <SidebarProvider defaultOpen={defaultOpen} className="flex-1">
        <AppSidebar />
        <SidebarInset className="min-w-0">
          <AppTopbar />
          {children}
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}
