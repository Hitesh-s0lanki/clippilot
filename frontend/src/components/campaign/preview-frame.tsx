import type { ReactNode } from "react";

import { AppLogo } from "@/components/layout/app-logo";
import { siteConfig } from "@/config/site";

export interface PreviewFrameProps {
  /** Sits above the card, small - the recipient is not a user of the product. */
  eyebrow?: string;
  children: ReactNode;
  /** Owner-only chrome: the preview banner, the recipient switcher. */
  toolbar?: ReactNode;
}

/**
 * The customer-facing shell.
 *
 * The only screen in the product that is not console chrome: one centred
 * column, no navigation, nothing to click but the video and the two answers.
 * A recipient arriving from an email has no account and no reason to be
 * offered a dashboard.
 */
export function PreviewFrame({ eyebrow, children, toolbar }: PreviewFrameProps) {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      {toolbar}
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-5 py-10">
        {eyebrow ? (
          <p className="mb-3 text-center text-sm text-muted-foreground">{eyebrow}</p>
        ) : null}
        {children}
      </main>
      <footer className="mx-auto flex w-full max-w-2xl items-center justify-center gap-2 px-5 pb-8">
        <AppLogo size={18} />
        <span className="text-xs text-muted-foreground">Delivered with {siteConfig.name}</span>
      </footer>
    </div>
  );
}
