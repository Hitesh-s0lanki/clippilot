import type { ReactNode } from "react";

export interface FormSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
}

/**
 * A titled block of fields.
 *
 * The flat counterpart to `BuilderSection`: no collapsing, because a form
 * short enough to read in one pass does not need progressive disclosure, and
 * an error hidden inside a collapsed panel is an error nobody can see.
 */
export function FormSection({ title, description, children }: FormSectionProps) {
  return (
    <section className="rounded-xl bg-card p-5 ring-1 ring-foreground/10">
      <div className="mb-4">
        <h2 className="font-heading font-semibold tracking-tight">{title}</h2>
        {description ? (
          <p className="mt-0.5 text-sm text-pretty text-muted-foreground">{description}</p>
        ) : null}
      </div>

      <div className="space-y-4">{children}</div>
    </section>
  );
}
