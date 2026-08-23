const CHECKS: ReadonlyArray<{ title: string; detail: string }> = [
  {
    title: "Is the API running?",
    detail: "Start it with `uv run uvicorn src.main:app --reload` from `backend/`.",
  },
  {
    title: "Did the address change?",
    detail: "A campaign that was deleted or archived no longer resolves at its old id.",
  },
  {
    title: "Still failing?",
    detail: "Quote the reference above - it matches this render in the server log.",
  },
];

/**
 * What usually fixes it, in the order worth trying.
 *
 * An error screen that only says "something went wrong" leaves the reader with
 * one move, the reload button. These are the three causes that account for
 * nearly every failure in this app, so the second move is obvious too.
 */
export function ErrorChecklist() {
  return (
    <ul className="mt-10 grid w-full gap-3 sm:grid-cols-3">
      {CHECKS.map(({ title, detail }) => (
        <li key={title} className="rounded-2xl border border-border bg-card p-5">
          <p className="font-heading text-sm font-semibold tracking-tight">{title}</p>
          <p className="mt-1.5 text-sm leading-relaxed text-pretty text-muted-foreground">
            {detail}
          </p>
        </li>
      ))}
    </ul>
  );
}
