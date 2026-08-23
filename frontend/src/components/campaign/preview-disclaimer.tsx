import { InfoIcon } from "lucide-react";

export interface PreviewDisclaimerProps {
  text: string;
}

/**
 * The regulatory disclaimer, beneath the video.
 *
 * Not optional dressing: for the brief's own financial-services scenario this
 * is what a real investment pitch legally carries. It is always visible rather
 * than folded into a disclosure, and it is never dismissible.
 */
export function PreviewDisclaimer({ text }: PreviewDisclaimerProps) {
  return (
    <div className="flex gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2.5">
      <InfoIcon aria-hidden className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
      <p className="text-xs leading-relaxed text-muted-foreground">{text}</p>
    </div>
  );
}
