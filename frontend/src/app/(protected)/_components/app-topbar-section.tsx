"use client";

import { usePathname } from "next/navigation";

import { activeSectionLabel } from "../_lib/nav-links";

/**
 * The name of the section the current URL sits in.
 *
 * It earns its place once the rail is collapsed to icons or hidden behind the
 * mobile sheet, which is exactly when the highlighted nav row stops being
 * readable. Read from the same module the rail is built from, so the two
 * can never disagree about what this screen is called.
 *
 * The divider is rendered here rather than by the bar, so a path that matches
 * no section leaves the bar with just its toggle instead of a rule with
 * nothing after it.
 */
export function AppTopbarSection() {
  const label = activeSectionLabel(usePathname());

  if (!label) return null;

  return (
    <>
      <span className="truncate text-sm font-medium">{label}</span>
    </>
  );
}
