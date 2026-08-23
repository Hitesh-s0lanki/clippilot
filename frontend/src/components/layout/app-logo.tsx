import Image from "next/image";

import { cn } from "@/lib/utils";

export interface AppLogoProps {
  /** Rendered edge length in px; the mark is square. */
  size?: number;
  className?: string;
}

/**
 * The ClipPilot mark.
 *
 * Renders `logo-mark.png` - the source illustration in `public/logo.png`
 * cropped to the clapperboard, because the popcorn, camera and chart around it
 * are unreadable below roughly 64px and only muddy the shape.
 *
 * The artwork has no alpha channel and sits on white, so it is framed as a
 * rounded tile the way an app icon is, rather than dropped straight onto the
 * header where it would glare as a white square in dark mode.
 *
 * Decorative: every place it appears, the name is already in the markup as
 * text, so announcing it again would only repeat the word.
 */
export function AppLogo({ size = 28, className }: AppLogoProps) {
  return (
    <Image
      src="/logo-mark.png"
      alt=""
      aria-hidden
      width={size}
      height={size}
      priority
      className={cn("rounded-lg border border-border/60 object-cover", className)}
    />
  );
}
