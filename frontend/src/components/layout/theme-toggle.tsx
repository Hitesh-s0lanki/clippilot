"use client";

import { MoonIcon, SunIcon } from "lucide-react";

import { ThemeMenuItems } from "@/components/layout/theme-menu-items";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ThemeToggle() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label="Change theme">
          {/*
            The resolved theme is only known in the browser, so the icon is
            swapped by the `dark` class rather than by state - rendering it from
            `theme` would disagree with the server-rendered markup.
          */}
          <SunIcon className="dark:hidden" />
          <MoonIcon className="hidden dark:block" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <ThemeMenuItems />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
