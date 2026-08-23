/**
 * A dotted field path -> the DOM id its input carries.
 *
 * The same string is used for `htmlFor`, `aria-describedby` and the focus call
 * that runs after a failed publish, so a field can be found from its API error
 * without a lookup table: `ads.0.options.1.label` is always
 * `field-experience-options-1-label`.
 */
export function fieldId(field: string): string {
  return `field-${field.replace(/\./g, "-")}`;
}

/** The id of the element carrying a field's error message. */
export function fieldErrorId(field: string): string {
  return `${fieldId(field)}-error`;
}
