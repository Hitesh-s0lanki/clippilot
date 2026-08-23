import { siteConfig } from "@/config/site";

/**
 * The four steps of the campaign journey, along the foot of the brand panel.
 *
 * Reads `siteConfig.flow` rather than restating the steps, so the account
 * screens and the landing page can never describe the product differently.
 * Two columns: the panel is wide, and a single column of four would leave the
 * copy stranded at the top.
 */
export function AuthFlowList() {
  return (
    <ol className="grid max-w-3xl grid-cols-2 gap-x-10 gap-y-7">
      {siteConfig.flow.map(({ step, title, description }) => (
        <li key={step} className="border-t border-border pt-4">
          <span className="font-mono text-xs font-medium text-primary">{step}</span>
          <h3 className="mt-1.5 font-heading text-sm font-semibold tracking-tight">{title}</h3>
          <p className="mt-1 text-sm leading-relaxed text-pretty text-muted-foreground">
            {description}
          </p>
        </li>
      ))}
    </ol>
  );
}
