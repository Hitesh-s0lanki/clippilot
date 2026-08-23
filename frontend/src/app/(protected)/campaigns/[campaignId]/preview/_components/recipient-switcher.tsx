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
import type { CampaignRecipient } from "@/types/campaign";

export interface RecipientSwitcherProps {
  recipients: CampaignRecipient[];
  selectedId: string;
}

/**
 * Switches which recipient the preview resolves against.
 *
 * The choice is written to the URL rather than held in state, so the preview
 * of one particular recipient is a link that can be sent to a colleague - and
 * so the server does the resolving, which is the only place it is authoritative.
 */
export function RecipientSwitcher({ recipients, selectedId }: RecipientSwitcherProps) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="preview-recipient" className="shrink-0 text-sm text-muted-foreground">
        Preview as
      </Label>
      <Select
        value={selectedId}
        onValueChange={(value) => router.push(`${pathname}?recipient_id=${value}`)}
      >
        <SelectTrigger id="preview-recipient" className="h-8 w-56">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {recipients.map((recipient) => (
            <SelectItem key={recipient.id} value={recipient.id}>
              {recipient.customer_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
