"use client";

import { useClerk, useUser } from "@clerk/nextjs";
import { ChevronsUpDownIcon, LogOutIcon, PaletteIcon, UserCogIcon } from "lucide-react";

import { ThemeMenuItems } from "@/components/layout/theme-menu-items";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

import { AppSidebarUserSkeleton } from "./app-sidebar-user-skeleton";
import { UserAvatar } from "./user-avatar";

/**
 * The account row pinned to the bottom of the sidebar.
 *
 * Everything that is about the person rather than about a campaign lives here:
 * who is signed in, their theme, Clerk's account panel and the way out. It is
 * the last row of the rail because that is where a console puts the account -
 * and because it keeps the nav above it about destinations only.
 *
 * Built on Clerk's hooks instead of embedding `<UserButton>`: the button
 * renders its own popover with its own styling, which cannot be widened into a
 * full-width sidebar row or taught about the theme options. `openUserProfile`
 * gives the same account management from a trigger we control.
 */
export function AppSidebarUser() {
  const { isMobile } = useSidebar();
  const { user, isLoaded } = useUser();
  const { openUserProfile, signOut } = useClerk();

  if (!isLoaded || !user) return <AppSidebarUserSkeleton />;

  const name = user.fullName ?? user.username ?? "Your account";
  const email = user.primaryEmailAddress?.emailAddress;

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg" className="gap-2.5">
              <UserAvatar imageUrl={user.hasImage ? user.imageUrl : undefined} name={name} />
              <span className="grid min-w-0 flex-1 text-left leading-tight">
                <span className="truncate text-sm font-medium">{name}</span>
                {email ? (
                  <span className="truncate text-xs text-muted-foreground">{email}</span>
                ) : null}
              </span>
              <ChevronsUpDownIcon aria-hidden className="ml-auto text-muted-foreground" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>

          <DropdownMenuContent
            // Matching the trigger's width keeps the menu aligned with the rail
            // instead of hanging off it; on mobile the rail is a sheet, so it
            // opens upward from the bottom of the screen instead.
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="flex items-center gap-2.5 py-2 font-normal">
              <UserAvatar imageUrl={user.hasImage ? user.imageUrl : undefined} name={name} />
              <span className="grid min-w-0 leading-tight">
                <span className="truncate text-sm font-medium">{name}</span>
                {email ? (
                  <span className="truncate text-xs text-muted-foreground">{email}</span>
                ) : null}
              </span>
            </DropdownMenuLabel>

            <DropdownMenuSeparator />

            <DropdownMenuItem onSelect={() => openUserProfile()}>
              <UserCogIcon />
              Manage account
            </DropdownMenuItem>

            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <PaletteIcon />
                Theme
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <ThemeMenuItems />
              </DropdownMenuSubContent>
            </DropdownMenuSub>

            <DropdownMenuSeparator />

            <DropdownMenuItem variant="destructive" onSelect={() => void signOut()}>
              <LogOutIcon />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
