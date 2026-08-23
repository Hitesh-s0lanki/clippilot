import { SidebarTrigger } from "@/components/ui/sidebar";

import { AppTopbarSection } from "./app-topbar-section";

/**
 * The thin bar above every console screen.
 *
 * Deliberately almost empty. Navigation moved to the rail, so all this owes the
 * user is a way to open or collapse it and a reminder of where they are -
 * anything more would rebuild the top nav the rail just replaced. It stays
 * stuck to the top so the sidebar toggle is reachable after a long scroll.
 */
export function AppTopbar() {
  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b border-border bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger className="-ml-1.5" />
      <AppTopbarSection />
    </header>
  );
}
