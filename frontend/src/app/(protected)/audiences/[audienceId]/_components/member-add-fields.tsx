"use client";

import type { ReactNode } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Gender } from "@/types/audience";
import { GENDER_LABELS, GENDER_ORDER } from "@/types/audience";

/** What the add form holds. Strings throughout - a form input's value is a string. */
export interface MemberFormValues {
  full_name: string;
  email: string;
  phone: string;
  age: string;
  gender: Gender;
  city: string;
  country: string;
  external_ref: string;
}

export const EMPTY_MEMBER_FORM: MemberFormValues = {
  full_name: "",
  email: "",
  phone: "",
  age: "",
  gender: "UNKNOWN",
  city: "",
  country: "",
  external_ref: "",
};

export interface MemberAddFieldsProps {
  values: MemberFormValues;
  onChange: (field: keyof MemberFormValues, value: string) => void;
}

/**
 * The fields of the add-a-person form.
 *
 * Every field except the name is labelled "(optional)" in so many words. The
 * usual convention marks the required ones instead, but here exactly one field
 * is required out of eight, and the honest reading of this form is that you
 * fill in whatever you happen to know.
 */
export function MemberAddFields({ values, onChange }: MemberAddFieldsProps) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="member-name">Name</Label>
        <Input
          id="member-name"
          value={values.full_name}
          onChange={(event) => onChange("full_name", event.target.value)}
          maxLength={80}
          required
          autoFocus
          aria-describedby="member-name-hint"
        />
        <p id="member-name-hint" className="text-xs text-muted-foreground">
          Resolves {"{{customer_name}}"} in the campaign message.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <OptionalField id="member-email" label="Email">
          <Input
            id="member-email"
            type="email"
            value={values.email}
            onChange={(event) => onChange("email", event.target.value)}
          />
        </OptionalField>

        <OptionalField id="member-phone" label="Phone">
          <Input
            id="member-phone"
            type="tel"
            value={values.phone}
            onChange={(event) => onChange("phone", event.target.value)}
            placeholder="+91 98765 43210"
          />
        </OptionalField>

        <OptionalField id="member-age" label="Age">
          <Input
            id="member-age"
            type="number"
            inputMode="numeric"
            min={13}
            max={120}
            value={values.age}
            onChange={(event) => onChange("age", event.target.value)}
          />
        </OptionalField>

        <OptionalField id="member-gender" label="Gender">
          <Select
            value={values.gender}
            onValueChange={(value) => onChange("gender", value as Gender)}
          >
            <SelectTrigger id="member-gender" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {GENDER_ORDER.map((gender) => (
                <SelectItem key={gender} value={gender}>
                  {GENDER_LABELS[gender]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </OptionalField>

        <OptionalField id="member-city" label="City">
          <Input
            id="member-city"
            value={values.city}
            onChange={(event) => onChange("city", event.target.value)}
          />
        </OptionalField>

        <OptionalField id="member-country" label="Country">
          <Input
            id="member-country"
            value={values.country}
            onChange={(event) => onChange("country", event.target.value)}
          />
        </OptionalField>
      </div>

      <OptionalField id="member-ref" label="CRM reference">
        <Input
          id="member-ref"
          value={values.external_ref}
          onChange={(event) => onChange("external_ref", event.target.value)}
          maxLength={120}
        />
      </OptionalField>
    </>
  );
}

function OptionalField({
  id,
  label,
  children,
}: {
  id: string;
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label} <span className="font-normal text-muted-foreground">(optional)</span>
      </Label>
      {children}
    </div>
  );
}
