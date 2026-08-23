"use client";

import { useEffect } from "react";

import "./globals.css";

/**
 * The last boundary: a failure in the root layout itself, which `error.tsx`
 * cannot catch because it sits inside that layout.
 *
 * It replaces the whole document, so it brings its own `<html>` and `<body>`
 * and imports the stylesheet directly. Two things the rest of the app has are
 * missing here by design and cannot be recovered: the `next/font` variables,
 * which the root layout sets on `<html>`, and the theme class that
 * `next-themes` writes there - so this always renders in the light palette
 * whatever the visitor picked. Metadata exports are not supported in a Client
 * Component, hence the plain `<title>`.
 */
export default function GlobalError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="flex min-h-dvh flex-col bg-background text-foreground">
        <title>Something went wrong · ClipPilot</title>
        <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-start justify-center px-5 py-20">
          <p className="font-mono text-sm font-medium text-destructive">Application error</p>
          <h1 className="mt-3 font-heading text-3xl font-semibold tracking-tight text-balance">
            ClipPilot could not start this page.
          </h1>
          <p className="mt-4 leading-relaxed text-pretty text-muted-foreground">
            The failure happened outside every screen, in the shell the app is built on. Reloading
            clears it in most cases; if it does not, the server log holds the detail.
          </p>

          {error.digest ? (
            <p className="mt-4 rounded-lg border border-border bg-muted/50 px-3 py-1.5 font-mono text-xs text-muted-foreground">
              Reference: {error.digest}
            </p>
          ) : null}

          <button
            type="button"
            onClick={retry}
            className="mt-8 inline-flex h-11 items-center justify-center rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/80 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            Reload the app
          </button>
        </main>
      </body>
    </html>
  );
}
