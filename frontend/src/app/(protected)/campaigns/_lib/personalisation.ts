/**
 * Client-side mirror of the API's variable resolver.
 *
 * Only for the builder's live preview - the value a recipient actually sees is
 * always resolved server-side. The rules are copied from
 * `backend/src/services/personalisation.py` so the preview under the textarea
 * cannot promise something the server would render differently: an unknown
 * variable is left literal rather than blanked, and a missing name falls back
 * to "there".
 */

const VARIABLE_PATTERN = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g;

export const KNOWN_VARIABLES = ["customer_name", "campaign_name"] as const;
export const MISSING_NAME_FALLBACK = "there";

const RESOLVABLE = new Set<string>([...KNOWN_VARIABLES, "option_label"]);

export interface ResolvedText {
  text: string;
  /** Variables the resolver cannot fill, so the builder can warn about them. */
  unresolved: string[];
}

export interface PersonalisationContext {
  customerName: string;
  campaignName: string;
}

export function resolveVariables(
  template: string,
  { customerName, campaignName }: PersonalisationContext,
): ResolvedText {
  const unresolved: string[] = [];
  const values: Record<string, string> = {
    customer_name: customerName.trim() || MISSING_NAME_FALLBACK,
    campaign_name: campaignName.trim(),
    option_label: "",
  };

  const text = template.replace(VARIABLE_PATTERN, (match, name: string) => {
    if (!RESOLVABLE.has(name)) {
      if (!unresolved.includes(name)) unresolved.push(name);
      return match;
    }
    return values[name];
  });

  return { text, unresolved };
}
