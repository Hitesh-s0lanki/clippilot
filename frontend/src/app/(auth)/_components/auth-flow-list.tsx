import { siteConfig } from "@/config/site";

/**
 * The four steps of the campaign journey, under the headline.
 *
 * Numbers and titles only. The steps each carry a sentence in `siteConfig`, and
 * the landing page is the right place to read them - here they would put four
 * more paragraphs beside a sign-in form, which is copy nobody signing in stops
 * to read. What the panel owes a visitor is the shape of the product, and four
 * words in order carry that.
 *
 * Reads `siteConfig.flow` rather than restating the steps, so the account
 * screens and the landing page can never disagree about the journey.
 */
export function AuthFlowList() {
  return (
    <ol className="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-4">
      {siteConfig.flow.map(({ step, title }) => (
        <li key={step} className="border-t border-border pt-3">
          <span className="font-mono text-xs font-medium text-primary">{step}</span>
          <h3 className="mt-1 font-heading text-sm font-semibold tracking-tight">{title}</h3>
        </li>
      ))}
    </ol>
  );
}
