import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AudienceMember } from "@/types/audience";
import { AGE_GROUP_LABELS, GENDER_LABELS } from "@/types/audience";

import { MemberRemoveButton } from "./member-remove-button";

export interface MemberTableProps {
  audienceId: string;
  members: AudienceMember[];
}

/**
 * The people themselves.
 *
 * Every column but the name can be empty, so a missing value renders as a dash
 * rather than a blank cell - the difference between "not given" and "the table
 * lost it" has to be visible, and a ragged upload is the normal case.
 *
 * The table scrolls inside its own container: eight columns do not fit a
 * phone, and the page body must never scroll sideways.
 */
export function MemberTable({ audienceId, members }: MemberTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl bg-card ring-1 ring-foreground/10">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>Age</TableHead>
            <TableHead>Gender</TableHead>
            <TableHead>City</TableHead>
            <TableHead>Country</TableHead>
            <TableHead>CRM ref</TableHead>
            <TableHead className="text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {members.map((member) => (
            <TableRow key={member.id}>
              <TableCell className="font-medium whitespace-nowrap">{member.full_name}</TableCell>
              <TableCell className="text-muted-foreground">
                <Optional value={member.email} />
              </TableCell>
              <TableCell className="whitespace-nowrap text-muted-foreground tabular-nums">
                <Optional value={member.phone} />
              </TableCell>
              <TableCell className="text-muted-foreground tabular-nums">
                {member.age === null ? (
                  <NotGiven />
                ) : (
                  <span title={AGE_GROUP_LABELS[member.age_group]}>{member.age}</span>
                )}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {member.gender === "UNKNOWN" ? <NotGiven /> : GENDER_LABELS[member.gender]}
              </TableCell>
              <TableCell className="text-muted-foreground">
                <Optional value={member.city} />
              </TableCell>
              <TableCell className="text-muted-foreground">
                <Optional value={member.country} />
              </TableCell>
              <TableCell className="text-muted-foreground">
                <Optional value={member.external_ref} />
              </TableCell>
              <TableCell className="text-right">
                <MemberRemoveButton
                  audienceId={audienceId}
                  memberId={member.id}
                  fullName={member.full_name}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

/** A value, or a dash that says the cell is empty on purpose. */
function Optional({ value }: { value: string | null }) {
  return value ? <>{value}</> : <NotGiven />;
}

function NotGiven() {
  return (
    <span aria-label="Not given" className="text-muted-foreground/60">
      —
    </span>
  );
}
