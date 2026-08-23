import type { ReactNode } from "react";

export interface PageHeaderProps {
  /** Small label above the title, naming the section the screen belongs to. */
  eyebrow?: string;
  title: string;
  description?: string;
  /** Primary actions, rendered right-aligned on desktop and below on mobile. */
  actions?: ReactNode;
}

/**
 * The heading block every console screen opens with.
 *
 * One component rather than a copied `<h1>` per page, so the type scale, the
 * gap under it and the wrap behaviour of the action row stay identical across
 * the dashboard, the builder and the analytics view.
 */
export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 space-y-1.5">
        {eyebrow ? <p className="text-sm font-medium text-primary">{eyebrow}</p> : null}
        <h1 className="font-heading text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
          {title}
        </h1>
        {description ? (
          <p className="max-w-prose leading-relaxed text-pretty text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}
