import { CircleAlertIcon, CircleCheckIcon, TriangleAlertIcon } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { probeHealth } from "@/lib/api";
import { cn } from "@/lib/utils";

/** One row: a coloured dot, a state, and the detail that state needs. */
function Pill({
  Icon,
  tone,
  label,
  detail,
}: {
  Icon: typeof CircleCheckIcon;
  tone: string;
  label: string;
  detail: string;
}) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      <span
        className={cn("inline-flex items-center gap-1.5 font-medium", tone)}
        // The dot repeats what the words already say, so it is decorative and
        // the state never rests on colour alone.
      >
        <Icon aria-hidden className="size-3.5" />
        {label}
      </span>
      <span className="text-muted-foreground">{detail}</span>
    </p>
  );
}

/**
 * A live probe of the backend, sized for the footer.
 *
 * It used to be a full card in the middle of the landing page, which put a
 * diagnostic where a marketing reader expects a product. Down here it still
 * answers the only question a visitor could have - is this thing running -
 * and, when it is not, says what to start.
 */
export async function ApiStatusPill() {
  const probe = await probeHealth();

  if (!probe.reachable) {
    return (
      <Pill
        Icon={CircleAlertIcon}
        tone="text-destructive"
        label="API unreachable"
        detail="Start the backend with `uv run uvicorn src.main:app --reload`."
      />
    );
  }

  const { health } = probe;

  return health.status === "ok" ? (
    <Pill
      Icon={CircleCheckIcon}
      tone="text-success"
      label="API connected"
      detail={`${health.service} v${health.version} · ${health.environment}`}
    />
  ) : (
    <Pill
      Icon={TriangleAlertIcon}
      tone="text-warning"
      label="API degraded"
      detail={`${health.service} v${health.version} · ${health.environment}`}
    />
  );
}

/** Holds the row's height while the probe streams in, so the footer cannot jump. */
export function ApiStatusPillSkeleton() {
  return <Skeleton aria-hidden className="h-4 w-56" />;
}
