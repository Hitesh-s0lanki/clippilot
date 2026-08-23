import { marketing } from "@/config/marketing";

/**
 * The strip between the hero and the first section.
 *
 * Not social proof - there is none to show honestly - but a factual answer to
 * "what does a campaign here actually carry", so the reader can place the
 * product before scrolling into the detail.
 */
export function LandingCapabilities() {
  return (
    <section aria-labelledby="capabilities-heading" className="pb-14 sm:pb-16">
      <h2 id="capabilities-heading" className="sr-only">
        What every campaign carries
      </h2>
      <ul className="flex flex-wrap gap-2">
        {marketing.capabilities.map(({ label, Icon }) => (
          <li
            key={label}
            className="inline-flex items-center gap-2 rounded-4xl border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground"
          >
            <Icon aria-hidden className="size-3.5 text-primary" />
            {label}
          </li>
        ))}
      </ul>
    </section>
  );
}
