import { ClockIcon, LinkIcon, VideoOffIcon } from "lucide-react";

export type PreviewUnavailableReason = "not-live" | "incomplete" | "unknown-link";

export interface PreviewUnavailableProps {
  reason: PreviewUnavailableReason;
}

const COPY = {
  "not-live": {
    Icon: ClockIcon,
    title: "This video isn’t available right now",
    body: "The campaign it belongs to is not running at the moment. If you were expecting something here, check back later or get in touch with whoever sent you the link.",
  },
  incomplete: {
    Icon: VideoOffIcon,
    title: "This video isn’t ready yet",
    body: "The campaign has not had its video added. Nothing is wrong with your link - there is simply nothing to play yet.",
  },
  "unknown-link": {
    Icon: LinkIcon,
    title: "This link doesn’t lead anywhere",
    body: "The video it pointed to has been removed, or the address was copied incompletely. Ask whoever sent it for a fresh link.",
  },
} as const;

/**
 * The recipient-facing dead ends.
 *
 * Written for the person holding the link, not for the person who built the
 * campaign: no status names, no campaign ids, no suggestion that they did
 * something wrong. A paused campaign is a decision someone else made.
 *
 * A missing campaign is handled here rather than by the app's own 404, which
 * carries console chrome and a "back to the console" button - neither of which
 * means anything to a recipient who has no account.
 */
export function PreviewUnavailable({ reason }: PreviewUnavailableProps) {
  const { Icon, title, body } = COPY[reason];

  return (
    <div className="flex flex-col items-center gap-3 rounded-xl bg-card px-6 py-14 text-center ring-1 ring-foreground/10">
      <span
        aria-hidden
        className="flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground"
      >
        <Icon className="size-5" />
      </span>
      <h1 className="font-heading text-lg font-medium">{title}</h1>
      <p className="max-w-sm leading-relaxed text-pretty text-muted-foreground">{body}</p>
    </div>
  );
}
