import { PlayIcon } from "lucide-react";

/**
 * A picture of the thing being sold: the page a recipient opens.
 *
 * Built from the same tokens as the real preview screen rather than a
 * screenshot, so it follows the palette into dark mode and stays sharp at any
 * density. Entirely decorative - every claim it makes is also made in the copy
 * beside it - so the whole block is hidden from assistive technology and the
 * mock controls are `span`s, not buttons a keyboard could land on.
 */
export function LandingHeroVisual() {
  return (
    <div aria-hidden className="relative mx-auto w-full max-w-sm lg:max-w-none">
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card shadow-xl shadow-primary/5">
        <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
          <span className="size-2 rounded-full bg-success" />
          <span className="text-xs font-medium text-muted-foreground">For Rahul</span>
          <span className="ml-auto font-mono text-[0.6875rem] tracking-wider text-muted-foreground uppercase">
            Live
          </span>
        </div>

        <div className="relative aspect-video bg-gradient-to-br from-primary/30 via-primary/15 to-chart-2/25">
          <span className="absolute inset-0 grid place-items-center">
            <span className="grid size-12 place-items-center rounded-full bg-background/85 shadow-sm backdrop-blur">
              <PlayIcon className="size-5 translate-x-px fill-primary text-primary" />
            </span>
          </span>
          <span className="absolute right-2 bottom-2 rounded-md bg-background/80 px-1.5 py-0.5 font-mono text-[0.6875rem] text-muted-foreground backdrop-blur">
            0:42
          </span>
        </div>

        {/* The bottom band is padding for the floating chip, which only
            appears from `sm` up - below that the card closes up instead. */}
        <div className="space-y-3 p-4 sm:pb-24">
          <p className="text-sm leading-relaxed">
            Hi <span className="rounded bg-primary/10 px-1 font-medium text-primary">Rahul</span>,
            we have identified an investment opportunity for you.
          </p>
          <div className="grid gap-2">
            <span className="flex h-9 items-center justify-center rounded-lg bg-primary text-xs font-medium text-primary-foreground">
              Tell me more
            </span>
            <span className="flex h-9 items-center justify-center rounded-lg border border-border text-xs font-medium">
              Not interested
            </span>
          </div>
          <p className="text-[0.6875rem] leading-relaxed text-muted-foreground">
            Investments are subject to market risk.
          </p>
        </div>
      </div>

      <div className="absolute bottom-3 -left-6 hidden rounded-2xl border border-border bg-card p-3 shadow-lg sm:block">
        <p className="text-[0.6875rem] font-medium tracking-wider text-muted-foreground uppercase">
          Response split
        </p>
        <p className="mt-1 font-heading text-lg font-semibold tracking-tight">62% / 38%</p>
        <span className="mt-1.5 flex h-1.5 w-28 overflow-hidden rounded-full bg-muted">
          <span className="w-[62%] bg-chart-1" />
          <span className="w-[38%] bg-chart-2" />
        </span>
      </div>
    </div>
  );
}
