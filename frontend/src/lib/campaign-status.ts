/**
 * Lifecycle presentation and the transitions the UI may offer.
 *
 * `status` is what the user chose; `effective_status` is what the campaign is
 * actually in right now, derived server-side from status + schedule +
 * completeness. The badge reads from `effective_status` - a "Published"
 * campaign that starts next Monday is not live, and saying "Active" would be a
 * lie. The transition table mirrors `backend/src/services/status_service.py`;
 * the server stays the authority and rejects anything this misses.
 */

import type { CampaignEffectiveStatus, CampaignStatus } from "@/types/campaign";

/** Badge variants defined in `src/components/ui/badge.tsx`. */
export type StatusTone = "secondary" | "outline" | "success" | "warning";

export interface StatusPresentation {
  label: string;
  tone: StatusTone;
  /** One line for the tooltip-free explanation under a heading. */
  description: string;
}

const PRESENTATION: Record<CampaignEffectiveStatus, StatusPresentation> = {
  INCOMPLETE: {
    label: "Incomplete",
    tone: "warning",
    description: "Saved as a draft, but not yet complete enough to publish.",
  },
  DRAFT: {
    label: "Draft",
    tone: "secondary",
    description: "Ready to publish. Nobody can open it yet.",
  },
  SCHEDULED: {
    label: "Scheduled",
    tone: "outline",
    description: "Published, and goes live when the start date arrives.",
  },
  ACTIVE: {
    label: "Active",
    tone: "success",
    description: "Live. Recipients can open it and respond right now.",
  },
  PAUSED: {
    label: "Paused",
    tone: "warning",
    description: "Published but closed to recipients until it is resumed.",
  },
  COMPLETED: {
    label: "Completed",
    tone: "secondary",
    description: "Past its end date. Analytics are final.",
  },
  ARCHIVED: {
    label: "Archived",
    tone: "outline",
    description: "Read-only. Archived campaigns cannot be edited or reopened.",
  },
};

export function statusPresentation(status: CampaignEffectiveStatus): StatusPresentation {
  return PRESENTATION[status] ?? PRESENTATION.DRAFT;
}

/** Only a live campaign can be opened by a recipient. */
export function isLive(status: CampaignEffectiveStatus): boolean {
  return status === "ACTIVE";
}

export function isArchived(status: CampaignStatus): boolean {
  return status === "ARCHIVED";
}

/**
 * The lifecycle moves a user may request, keyed by the persisted status.
 *
 * Time-driven moves (`SCHEDULED -> ACTIVE -> COMPLETED`) are derived rather
 * than requested, so they are absent here on purpose.
 */
const ALLOWED_TRANSITIONS: Record<CampaignStatus, CampaignStatus[]> = {
  DRAFT: ["ACTIVE", "ARCHIVED"],
  SCHEDULED: ["PAUSED", "DRAFT", "ARCHIVED"],
  ACTIVE: ["PAUSED", "DRAFT", "ARCHIVED"],
  PAUSED: ["ACTIVE", "ARCHIVED"],
  COMPLETED: ["ARCHIVED"],
  ARCHIVED: [],
};

export function canTransition(from: CampaignStatus, to: CampaignStatus): boolean {
  return ALLOWED_TRANSITIONS[from]?.includes(to) ?? false;
}

export interface LifecycleActions {
  canPublish: boolean;
  canPause: boolean;
  canResume: boolean;
  /** Back to draft. The server refuses once the campaign has recorded events. */
  canUnpublish: boolean;
  canArchive: boolean;
  canEdit: boolean;
}

export function lifecycleActions(status: CampaignStatus): LifecycleActions {
  return {
    canPublish: canTransition(status, "ACTIVE") && status === "DRAFT",
    canPause: canTransition(status, "PAUSED"),
    canResume: status === "PAUSED",
    canUnpublish: canTransition(status, "DRAFT"),
    canArchive: canTransition(status, "ARCHIVED"),
    canEdit: status !== "ARCHIVED",
  };
}
