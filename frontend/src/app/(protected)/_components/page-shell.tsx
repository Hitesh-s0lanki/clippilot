import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export type PageShellProps = ComponentProps<"div">;

/**
 * The content column of every console screen.
 *
 * A `div`, not a `main`: `SidebarInset` already renders the group's `<main>`
 * landmark, and a second one nested inside it is invalid HTML and gives a
 * screen reader two "main" regions to choose between.
 *
 * One component rather than the same six utilities repeated in each page, so
 * the gutter and the measure stay identical from the dashboard to the builder
 * to an error boundary - a screen that is 40px narrower than its neighbour
 * reads as a bug even when nobody can say why.
 */
export function PageShell({ className, ...props }: PageShellProps) {
  return (
    <div
      className={cn("mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:py-10", className)}
      {...props}
    />
  );
}
