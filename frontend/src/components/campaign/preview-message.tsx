export interface PreviewMessageProps {
  headline: string | null;
  /** The ad's supporting line, beneath the headline. Already resolved. */
  description?: string | null;
  /** Already resolved server-side - `{{customer_name}}` is gone by now. */
  message: string;
}

/**
 * The headline and the personalised message.
 *
 * Rendered as text, never as markup: the customer name inside it came from a
 * form, and interpolating untrusted input into HTML is how a campaign builder
 * becomes an XSS delivery mechanism. React escapes it here by default.
 */
export function PreviewMessage({ headline, description, message }: PreviewMessageProps) {
  return (
    <div className="space-y-2 text-center">
      {headline ? (
        <h1 className="font-heading text-xl font-semibold tracking-tight text-balance sm:text-2xl">
          {headline}
        </h1>
      ) : null}
      {description ? (
        <p className="text-sm text-pretty text-muted-foreground/80">{description}</p>
      ) : null}
      <p className="text-base leading-relaxed text-pretty text-muted-foreground sm:text-lg">
        {message}
      </p>
    </div>
  );
}
