"use client";

import { MonitorIcon, MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";

import { DropdownMenuRadioGroup, DropdownMenuRadioItem } from "@/components/ui/dropdown-menu";

const OPTIONS = [
  { value: "light", label: "Light", Icon: SunIcon },
  { value: "dark", label: "Dark", Icon: MoonIcon },
  { value: "system", label: "System", Icon: MonitorIcon },
] as const;

/**
 * The three theme choices, as menu rows.
 *
 * Extracted so the header's `ThemeToggle` and the sidebar's account menu offer
 * the same options in the same order - two copies of this list is how "System"
 * ends up missing from one of them.
 *
 * A radio group rather than a toggle: "system" is a third state, not the
 * absence of the other two, and only a radio group can say which one is
 * currently chosen.
 */
export function ThemeMenuItems() {
  const { theme, setTheme } = useTheme();

  return (
    <DropdownMenuRadioGroup value={theme ?? "system"} onValueChange={setTheme}>
      {OPTIONS.map(({ value, label, Icon }) => (
        <DropdownMenuRadioItem key={value} value={value}>
          <Icon />
          {label}
        </DropdownMenuRadioItem>
      ))}
    </DropdownMenuRadioGroup>
  );
}
