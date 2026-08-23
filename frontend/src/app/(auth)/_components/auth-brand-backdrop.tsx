/**
 * The wash of colour behind the brand panel.
 *
 * Three stacked layers - a diagonal tint plus two blurred brand-hue orbs -
 * rather than an image, so it costs nothing to load and follows the palette
 * into dark mode instead of staying a fixed light-mode picture. Purely
 * decorative, so it is hidden from assistive technology.
 */
export function AuthBrandBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/12 via-transparent to-chart-2/10" />
      <div className="absolute -top-40 -left-32 size-[32rem] rounded-full bg-primary/20 blur-3xl" />
      <div className="absolute -bottom-48 left-1/3 size-[36rem] rounded-full bg-chart-2/15 blur-3xl" />
    </div>
  );
}
