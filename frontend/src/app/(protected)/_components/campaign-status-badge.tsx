import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { statusPresentation } from "@/lib/campaign-status";
import type { CampaignEffectiveStatus } from "@/types/campaign";

export interface CampaignStatusBadgeProps {
  status: CampaignEffectiveStatus;
  className?: string;
}

/**
 * The lifecycle badge, read from `effective_status`.
 *
 * Colour never carries the meaning on its own - every tone ships with its own
 * word, so the badge still reads correctly in greyscale and to anyone who does
 * not distinguish the hues.
 */
export function CampaignStatusBadge({ status, className }: CampaignStatusBadgeProps) {
  const { label, tone } = statusPresentation(status);

  return (
    <Badge variant={tone} className={cn("gap-1.5", className)}>
      <span
        aria-hidden
        className={cn(
          "size-1.5 rounded-full",
          tone === "success" && "bg-success",
          tone === "warning" && "bg-warning",
          tone === "outline" && "bg-primary",
          tone === "secondary" && "bg-muted-foreground",
        )}
      />
      {label}
    </Badge>
  );
}
