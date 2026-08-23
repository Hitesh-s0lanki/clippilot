"use client";

import { BarChart3Icon, LayersIcon, PencilIcon, PlayCircleIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

export interface CampaignTabsProps {
  campaignId: string;
}

const TABS = [
  { segment: "edit", label: "Builder", Icon: PencilIcon },
  { segment: "ads", label: "Ads", Icon: LayersIcon },
  { segment: "preview", label: "Preview", Icon: PlayCircleIcon },
  { segment: "analytics", label: "Analytics", Icon: BarChart3Icon },
] as const;

/**
 * The four views of one campaign.
 *
 * The audience is deliberately not among them. It is account-level and shared
 * by any number of campaigns, so editing it from inside one would quietly edit
 * it for the rest - the builder selects a list, and the list is managed on its
 * own screen.
 *
 * Links rather than a tab widget: each view is a real URL that can be shared
 * and returned to, and the browser's back button should move between them.
 * `aria-current` carries the active state, and the underline carries it
 * visually so it does not rest on colour alone.
 */
export function CampaignTabs({ campaignId }: CampaignTabsProps) {
  const pathname = usePathname();

  return (
    <nav aria-label="Campaign views" className="flex gap-1 border-b border-border">
      {TABS.map(({ segment, label, Icon }) => {
        const href = `/campaigns/${campaignId}/${segment}`;
        const active = pathname === href;

        return (
          <Link
            key={segment}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "-mb-px inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
              active
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:border-border hover:text-foreground",
            )}
          >
            <Icon aria-hidden className="size-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
