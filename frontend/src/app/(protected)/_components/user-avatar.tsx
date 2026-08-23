import Image from "next/image";

import { cn } from "@/lib/utils";

export interface UserAvatarProps {
  /** Clerk's `user.imageUrl`, or `undefined` when the account has no picture. */
  imageUrl?: string;
  /** Used for the initials fallback and for nothing else - never announced. */
  name: string;
  className?: string;
}

/** First letters of the first two words, e.g. "Ada Lovelace" -> "AL". */
function initials(name: string): string {
  const letters = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? "");

  return letters.join("") || "?";
}

/**
 * The account picture in the sidebar footer.
 *
 * Decorative in both branches: the name sits next to it as text in every place
 * this is used, so an `alt` would only make a screen reader read the name
 * twice. When Clerk has no picture this draws initials rather than a generic
 * silhouette - a letter tile identifies which account is signed in, a grey
 * person icon does not.
 */
export function UserAvatar({ imageUrl, name, className }: UserAvatarProps) {
  const base = cn("size-8 shrink-0 rounded-lg object-cover", className);

  if (imageUrl) {
    return <Image src={imageUrl} alt="" aria-hidden width={32} height={32} className={base} />;
  }

  return (
    <span
      aria-hidden
      className={cn(
        base,
        "flex items-center justify-center bg-primary/10 text-xs font-semibold text-primary",
      )}
    >
      {initials(name)}
    </span>
  );
}
