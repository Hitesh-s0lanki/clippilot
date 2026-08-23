"use client";

import Image from "next/image";
import { useState } from "react";

export interface AdsPosterImageProps {
  src: string;
}

/**
 * The poster itself, and the only client code on this screen.
 *
 * The URL is whatever the campaign owner typed - the API validates its scheme
 * and host, but nothing guarantees it still resolves. Without `onError` a dead
 * one leaves Chrome's broken-image glyph sitting in the corner of the card; on
 * failure this unmounts instead, so the gradient behind it becomes the cover
 * and the grid looks deliberate either way.
 *
 * `alt=""` because the card's heading names the campaign right underneath.
 * `unoptimized` because the image is not ours: routing a third-party URL
 * through the optimiser adds a way for it to fail without making it smaller.
 */
export function AdsPosterImage({ src }: AdsPosterImageProps) {
  const [broken, setBroken] = useState(false);

  if (broken) return null;

  return (
    <Image
      src={src}
      alt=""
      aria-hidden
      fill
      unoptimized
      sizes="(min-width: 1024px) 320px, (min-width: 640px) 45vw, 90vw"
      className="object-cover"
      onError={() => setBroken(true)}
    />
  );
}
