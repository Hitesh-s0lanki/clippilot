import Link from "next/link";

import { siteConfig } from "@/config/site";

type FooterColumn = (typeof siteConfig.footerNav)[number];

export interface PublicFooterNavProps {
  column: FooterColumn;
}

/** One titled column of the footer. The `<h3>` labels the `<nav>` for screen readers. */
export function PublicFooterNav({ column }: PublicFooterNavProps) {
  const headingId = `footer-${column.title.toLowerCase()}`;

  return (
    <nav aria-labelledby={headingId}>
      <h3 id={headingId} className="text-sm font-semibold tracking-tight">
        {column.title}
      </h3>
      <ul className="mt-3 space-y-2.5">
        {column.links.map(({ label, href }) => (
          <li key={href}>
            <Link
              href={href}
              className="rounded-sm text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
