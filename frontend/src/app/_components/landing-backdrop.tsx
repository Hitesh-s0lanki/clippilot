/**
 * The wash of colour behind the hero.
 *
 * Three stacked layers - a diagonal tint and two blurred brand-hue orbs -
 * rather than an image, so it costs nothing to load and follows the palette
 * into dark mode instead of staying a fixed light-mode picture. The same
 * technique as the account screens' backdrop, tuned for a full-width band.
 * Purely decorative, so it is hidden from assistive technology.
 */
export function LandingBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-chart-2/10" />
      <div className="absolute -top-56 -left-40 size-[36rem] rounded-full bg-primary/20 blur-3xl" />
      <div className="absolute -top-32 -right-48 size-[34rem] rounded-full bg-chart-2/15 blur-3xl" />
      <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-background to-transparent" />
    </div>
  );
}
