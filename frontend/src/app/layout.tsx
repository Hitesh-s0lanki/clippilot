import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { ThemeProvider } from "@/components/layout/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { siteConfig } from "@/config/site";
import { env } from "@/lib/env";

import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: siteConfig.title, template: `%s · ${siteConfig.name}` },
  description: siteConfig.description,
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#131318" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // next-themes writes the theme class before paint, so the server markup
    // and the first client render differ by design on <html> alone.
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="flex min-h-dvh flex-col">
        {/*
         * Providers only. Chrome is not rendered here on purpose: a global
         * header would put "Sign in" and "Get started" buttons on top of the
         * sign-in page itself, so each group brings its own - `(protected)`
         * the app shell, the landing page its own, `(auth)` none at all.
         *
         * Core 3 requires ClerkProvider inside <body>, not around <html>. It
         * sits above ThemeProvider so every group shares one Clerk context.
         * Sign-in and sign-up URLs come from the environment (see
         * `env.authRoutes`) because the server helpers read them there; only
         * the sign-out destination has no env var of its own.
         */}
        <ClerkProvider afterSignOutUrl={env.authRoutes.afterSignOut}>
          <ThemeProvider>
            {children}
            <Toaster />
          </ThemeProvider>
        </ClerkProvider>
      </body>
    </html>
  );
}
