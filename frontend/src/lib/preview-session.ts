const STORAGE_PREFIX = "clippilot:preview-session:";

function createSessionId(): string {
  // The API accepts 8-64 characters of alphanumerics, dashes or underscores.
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
}

/**
 * The identifier that makes one preview one session.
 *
 * It is the server's deduplication key: a view and a response are each
 * recorded once per session, enforced by a unique index rather than only by
 * the UI, so a double-click or a refresh cannot inflate the numbers.
 * `sessionStorage` is what makes a refresh part of the same session while a
 * new tab starts a new one.
 *
 * Deliberately a plain function rather than a hook. The id is random, so
 * producing it during render would differ between the server pass and the
 * browser pass - a hydration mismatch on every preview. Nothing renders it,
 * though: it is only needed at the moment an event is recorded, which is
 * always inside a browser event handler.
 */
export function getPreviewSessionId(campaignId: string): string {
  const key = `${STORAGE_PREFIX}${campaignId}`;

  try {
    const existing = window.sessionStorage.getItem(key);
    if (existing) return existing;

    const created = createSessionId();
    window.sessionStorage.setItem(key, created);
    return created;
  } catch {
    // Private mode, or storage disabled. Deduplication still holds for the
    // life of this page, which is the case that matters for a double-click.
    return createSessionId();
  }
}
