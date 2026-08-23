"use client";

import { usePathname, useRouter } from "next/navigation";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AudienceMember } from "@/types/audience";

export interface RecipientSwitcherProps {
  members: AudienceMember[];
  selectedId: string;
}

/**
 * Switches which member the preview resolves against.
 *
 * The choice is written to the URL rather than held in state, so the preview
 * of one particular member is a link that can be sent to a colleague - and
 * so the server does the resolving, which is the only place it is authoritative.
 */
export function MemberSwitcher({ members, selectedId }: RecipientSwitcherProps) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="preview-member" className="shrink-0 text-sm text-muted-foreground">
        Preview as
      </Label>
      <Select
        value={selectedId}
        onValueChange={(value) => router.push(`${pathname}?member_id=${value}`)}
      >
        <SelectTrigger id="preview-member" className="h-8 w-56">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {members.map((member) => (
            <SelectItem key={member.id} value={member.id}>
              {member.full_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
