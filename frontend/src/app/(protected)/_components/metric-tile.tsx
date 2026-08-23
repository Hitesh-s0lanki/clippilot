import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export interface MetricTileProps {
  label: string;
  /** Already formatted - the tile never divides, rounds or guesses a unit. */
  value: string;
  hint?: string;
  icon?: LucideIcon;
  /** `lead` is the objective's headline number, set once per screen. */
  emphasis?: "default" | "lead";
}

/**
 * One number with its label.
 *
 * Shared by the dashboard summary and the analytics grid so the same metric
 * never appears at two sizes on two screens.
 */
export function MetricTile({
  label,
  value,
  hint,
  icon: Icon,
  emphasis = "default",
}: MetricTileProps) {
  const lead = emphasis === "lead";

  return (
    <div
      className={cn(
        "rounded-xl bg-card p-4 ring-1 ring-foreground/10",
        lead && "bg-primary/5 ring-primary/20",
      )}
    >
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        {Icon ? <Icon aria-hidden className="size-3.5" /> : null}
        <span className="truncate">{label}</span>
      </div>
      <p
        className={cn(
          "mt-2 font-heading font-semibold tracking-tight tabular-nums",
          lead ? "text-3xl text-primary sm:text-4xl" : "text-2xl",
        )}
      >
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
