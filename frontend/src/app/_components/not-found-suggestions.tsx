import { LayoutGridIcon, type LucideIcon, PlusIcon, SparklesIcon } from "lucide-react";
import Link from "next/link";

const SUGGESTIONS: ReadonlyArray<{
  href: string;
  title: string;
  description: string;
  Icon: LucideIcon;
}> = [
  {
    href: "/dashboard",
    title: "Campaign dashboard",
    description: "Every campaign you own, with its status and counters.",
    Icon: LayoutGridIcon,
  },
  {
    href: "/campaigns/new",
    title: "Create a campaign",
    description: "Start a new personalised video journey from an empty builder.",
    Icon: PlusIcon,
  },
  {
    href: "/#how-it-works",
    title: "How ClipPilot works",
    description: "The four steps from a draft to a recorded response.",
    Icon: SparklesIcon,
  },
];

/**
 * Where to go instead.
 *
 * A dead end is only useful if it offers a way out, so the 404 carries the
 * three destinations that cover almost every reason someone was here. The
 * console links sit behind the session guard - a signed-out visitor following
 * one is sent to sign-in, not to another 404.
 */
export function NotFoundSuggestions() {
  return (
    <nav aria-label="Suggested destinations" className="mt-10 w-full">
      <ul className="grid gap-3 sm:grid-cols-3">
        {SUGGESTIONS.map(({ href, title, description, Icon }) => (
          <li key={href}>
            <Link
              href={href}
              className="flex h-full flex-col rounded-2xl border border-border bg-card p-5 transition-colors hover:border-primary/40 hover:bg-accent focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              <Icon aria-hidden className="size-5 text-primary" />
              <span className="mt-3 font-heading font-semibold tracking-tight">{title}</span>
              <span className="mt-1 text-sm leading-relaxed text-pretty text-muted-foreground">
                {description}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
