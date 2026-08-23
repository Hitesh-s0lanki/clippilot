/**
 * The result contract every Server Action in this app returns.
 *
 * Actions resolve to this rather than throwing, because the caller is a form
 * that has to render the failure next to the field that caused it. Throwing
 * would hand the problem to the route's error boundary and replace the whole
 * screen - which is right for a bug, and wrong for "that name is taken".
 */
export type ActionResult<T = void> =
  | { ok: true; data: T }
  | {
      ok: false;
      /** The backend's error code, e.g. `VALIDATION_ERROR`. */
      code: string;
      message: string;
      /** Dotted field path -> first message, ready to hand to a form. */
      fieldErrors: Record<string, string>;
    };
