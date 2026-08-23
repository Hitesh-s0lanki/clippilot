import { ArrowLeftIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { AppLogo } from "@/components/layout/app-logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { siteConfig } from "@/config/site";

export interface AuthFormPanelProps {
  children: ReactNode;
}

/**
 * The narrow half of the account screens - the fourth column of the split.
 *
 * It frames Clerk's card with the two controls the missing site header would
 * otherwise have provided: a way back to the landing page, and the theme
 * toggle. Without them the account screens would be the only place in the app
 * where a visitor can neither leave nor switch to dark mode.
 *
 * The mark repeats here only below `xl`, where the brand panel is hidden and
 * nothing else identifies the product.
 */
export function AuthFormPanel({ children }: AuthFormPanelProps) {
  return (
    <main className="flex min-w-0 flex-col px-5 py-6 sm:px-8">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-lg outline-none focus-visible:ring-3 focus-visible:ring-ring/50 xl:hidden"
        >
          <AppLogo size={28} />
          <span className="font-heading font-semibold tracking-tight">{siteConfig.name}</span>
        </Link>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>

      {/*
        `data-auth-form` is the hook the unlayered rule in `globals.css` uses to
        let Clerk's card track this column instead of overflowing it. That rule
        applies at every width, so the cap here is what stops the card spreading
        across the single-column layout below `xl`, or across an ultrawide
        column above it: 25rem is the width Clerk sizes the card to by itself.
      */}
      <div
        data-auth-form=""
        className="mx-auto flex w-full max-w-100 flex-1 flex-col justify-center py-10 sm:py-12"
      >
        {children}
      </div>

      <Link
        href="/"
        className="inline-flex items-center justify-center gap-1.5 self-center rounded-lg px-2 py-1 text-sm text-muted-foreground transition-colors outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <ArrowLeftIcon className="size-3.5" />
        Back to {siteConfig.name}
      </Link>
    </main>
  );
}
