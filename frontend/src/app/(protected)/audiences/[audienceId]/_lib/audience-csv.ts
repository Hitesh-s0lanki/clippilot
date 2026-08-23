import type { AudienceMember, AudienceMemberInput, Gender } from "@/types/audience";

/**
 * Reading and writing the audience file format.
 *
 * The rule the whole module is built around: **only a name is required**. A
 * real exported list is ragged - some rows carry an email, some a phone, some
 * an age and nothing else - and a parser that refuses a row over a missing
 * cell is a parser nobody can upload to.
 */

/** The columns, in the order they are written on export. */
export const CSV_COLUMNS = [
  "full_name",
  "email",
  "phone",
  "age",
  "gender",
  "city",
  "country",
  "external_ref",
] as const;

type Column = (typeof CSV_COLUMNS)[number];

/**
 * Header spellings accepted on import.
 *
 * Generous on purpose: the file comes out of somebody's CRM or spreadsheet,
 * not out of this app. `customer_name` is here because that is what the column
 * used to be called, so an older export still imports.
 */
const HEADER_ALIASES: Record<string, Column> = {
  full_name: "full_name",
  "full name": "full_name",
  name: "full_name",
  customer_name: "full_name",
  "customer name": "full_name",
  email: "email",
  email_address: "email",
  "email address": "email",
  phone: "phone",
  phone_number: "phone",
  "phone number": "phone",
  mobile: "phone",
  age: "age",
  gender: "gender",
  sex: "gender",
  city: "city",
  town: "city",
  country: "country",
  external_ref: "external_ref",
  "external ref": "external_ref",
  crm_id: "external_ref",
  reference: "external_ref",
};

/** What people actually type in a gender column, folded to the enum. */
const GENDER_ALIASES: Record<string, Gender> = {
  f: "FEMALE",
  female: "FEMALE",
  woman: "FEMALE",
  m: "MALE",
  male: "MALE",
  man: "MALE",
  o: "OTHER",
  other: "OTHER",
  "non-binary": "OTHER",
  nonbinary: "OTHER",
};

/*
 * Mirrors `backend/src/schemas/audience.py`.
 *
 * Checked here as well as there so a bad row can be named by its line number:
 * the API reports the index it was sent, which means nothing to someone
 * looking at a spreadsheet.
 */
const MAX_NAME = 80;
const MAX_EXTERNAL_REF = 120;
const MAX_PLACE = 56;
const MIN_AGE = 13;
const MAX_AGE = 120;
/** The server's own pattern - digits only, optional `+`, no separators. */
const PHONE = /^\+?[1-9]\d{6,19}$/;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** The API's `max_length` on the members array of one call. */
export const MAX_MEMBERS_PER_UPLOAD = 1000;

/**
 * Drops the separators people type into spreadsheets.
 *
 * `+91 98765 43210` and `(555) 123-4567` are both a phone number to a human
 * and both rejected by the server's pattern. Stripping spaces, dashes, dots
 * and brackets is unambiguous - it never changes which number is meant.
 */
function normalisePhone(value: string): string {
  return value.replace(/[\s().-]/g, "");
}

export interface CsvSkip {
  /** 1-based line in the uploaded file, so the message points at something real. */
  line: number;
  reason: string;
}

export interface ParsedMemberRow {
  /**
   * The line this came from, carried through so later checks can name it.
   *
   * It cannot be recovered from the row's position: rejected lines are not in
   * `rows`, so the third surviving row may well be the sixth line of the file.
   */
  line: number;
  member: AudienceMemberInput;
}

export interface ParsedMembers {
  rows: ParsedMemberRow[];
  skipped: CsvSkip[];
  /** Set when the file could not be read as a list of people at all. */
  error?: string;
}

/**
 * Splits CSV text into rows of cells.
 *
 * A hand-rolled reader rather than a dependency: the format here is a handful
 * of short text columns, and the only parts of RFC 4180 that matter are quoted
 * cells containing commas, newlines or escaped quotes - which a `split(",")`
 * would silently corrupt into shifted columns. Accepts LF and CRLF.
 */
function readCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];

    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          cell += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        cell += char;
      }
      continue;
    }

    if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(cell);
      cell = "";
    } else if (char === "\n" || char === "\r") {
      // A CRLF pair closes one row, not two.
      if (char === "\r" && text[i + 1] === "\n") i += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  if (cell !== "" || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }

  return rows;
}

function blankToNull(value: string | undefined): string | null {
  const trimmed = value?.trim() ?? "";
  return trimmed === "" ? null : trimmed;
}

/**
 * Reads an uploaded list of people.
 *
 * Every rejected line is reported with its number and reason rather than
 * dropped, because a silent import that lands 8 of 10 rows is worse than one
 * that refuses: the user has no way to notice the two that vanished.
 *
 * A row is only ever rejected for something that would make the *whole call*
 * fail - a malformed email or phone, a name that is too long. An unreadable
 * age or an unrecognised gender costs that one cell, not the person: dropping
 * someone from a campaign because their age column said "n/a" would be absurd.
 */
export function parseMemberCsv(text: string): ParsedMembers {
  const rows = readCsv(text).filter((cells) => cells.some((cell) => cell.trim() !== ""));

  if (rows.length === 0) {
    return { rows: [], skipped: [], error: "That file is empty." };
  }

  const header = rows[0].map((cell) => cell.trim().toLowerCase().replace(/^﻿/, ""));
  const columns = header.map((cell) => HEADER_ALIASES[cell]);

  if (!columns.includes("full_name")) {
    return {
      rows: [],
      skipped: [],
      error: 'No name column. The file needs a header row with a "full_name" (or "name") column.',
    };
  }

  const parsed: ParsedMemberRow[] = [];
  const skipped: CsvSkip[] = [];
  const seenEmails = new Set<string>();

  rows.slice(1).forEach((cells, index) => {
    const line = index + 2; // +1 for the header, +1 for 1-based counting.
    const field = (name: Column) => {
      const at = columns.indexOf(name);
      return at === -1 ? null : blankToNull(cells[at]);
    };

    const fullName = field("full_name");
    if (!fullName) {
      skipped.push({ line, reason: "no name" });
      return;
    }
    if (fullName.length > MAX_NAME) {
      skipped.push({ line, reason: `name is longer than ${MAX_NAME} characters` });
      return;
    }

    const email = field("email");
    if (email) {
      if (!EMAIL.test(email)) {
        skipped.push({ line, reason: `${email} is not a valid email address` });
        return;
      }
      const key = email.toLowerCase();
      // The API holds email unique per audience, so a file that repeats one
      // would lose that row server-side with only an index to explain it.
      // Catching it here names the line instead.
      if (seenEmails.has(key)) {
        skipped.push({ line, reason: `${email} appears more than once in this file` });
        return;
      }
      seenEmails.add(key);
    }

    const rawPhone = field("phone");
    const phone = rawPhone === null ? null : normalisePhone(rawPhone);
    if (phone !== null && !PHONE.test(phone)) {
      skipped.push({ line, reason: `${rawPhone} is not a usable phone number` });
      return;
    }

    const externalRef = field("external_ref");
    if (externalRef && externalRef.length > MAX_EXTERNAL_REF) {
      skipped.push({ line, reason: `reference is longer than ${MAX_EXTERNAL_REF} characters` });
      return;
    }

    // Optional segmentation cells: unreadable means "not given", never a
    // rejected person.
    const rawAge = field("age");
    const age = rawAge === null ? null : Number.parseInt(rawAge, 10);
    const usableAge = age !== null && Number.isFinite(age) && age >= MIN_AGE && age <= MAX_AGE;

    const rawGender = field("gender");
    const gender = rawGender ? GENDER_ALIASES[rawGender.toLowerCase()] : undefined;

    const place = (value: string | null) => (value && value.length <= MAX_PLACE ? value : null);

    parsed.push({
      line,
      member: {
        full_name: fullName,
        email,
        phone,
        age: usableAge ? age : null,
        gender: gender ?? "UNKNOWN",
        city: place(field("city")),
        country: place(field("country")),
        external_ref: externalRef,
      },
    });
  });

  return { rows: parsed, skipped };
}

/** Wraps a cell only when it would otherwise break the row. */
function escapeCell(value: string | number | null): string {
  const text = value === null ? "" : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/**
 * Writes a list back out.
 *
 * Round-trips: the header uses the canonical column names, so an exported file
 * can be edited in a spreadsheet and imported again without remapping. `id`
 * and `created_at` are deliberately absent - exporting them would invite
 * someone to edit and re-import a file claiming identities the server never
 * issued.
 */
export function toMemberCsv(members: AudienceMember[]): string {
  const lines = [
    CSV_COLUMNS.join(","),
    ...members.map((member) =>
      [
        escapeCell(member.full_name),
        escapeCell(member.email),
        escapeCell(member.phone),
        escapeCell(member.age),
        escapeCell(member.gender === "UNKNOWN" ? null : member.gender),
        escapeCell(member.city),
        escapeCell(member.country),
        escapeCell(member.external_ref),
      ].join(","),
    ),
  ];

  // A trailing newline - POSIX text convention, and some spreadsheet importers
  // drop the last row without it.
  return `${lines.join("\r\n")}\r\n`;
}

/* -------------------------------------------------------------------------
 * The sample file
 * ---------------------------------------------------------------------- */

/** What the sample downloads as. */
export const SAMPLE_CSV_FILENAME = "audience-sample.csv";

/**
 * Three rows chosen to answer the questions the format actually raises,
 * rather than three rows of filler.
 *
 * Row 1 is complete, so the header maps onto something. Row 2 is a name and
 * nothing else, which is the point people most need to see: a ragged file is
 * the expected file, not a broken one. Row 3 carries the awkward cases -
 * a phone with brackets and spaces, a one-letter gender, a city containing a
 * comma - all of which the parser handles, and none of which anyone would
 * risk in their own file without having seen it work.
 */
const SAMPLE_ROWS: Record<Column, string>[] = [
  {
    full_name: "Priya Sharma",
    email: "priya.sharma@example.com",
    phone: "+91 98765 43210",
    age: "32",
    gender: "female",
    city: "Mumbai",
    country: "India",
    external_ref: "CRM-10241",
  },
  {
    full_name: "Daniel Okoye",
    email: "",
    phone: "",
    age: "",
    gender: "",
    city: "",
    country: "",
    external_ref: "",
  },
  {
    full_name: "Mei Chen",
    email: "mei.chen@example.com",
    phone: "(415) 555-0132",
    age: "27",
    gender: "F",
    city: "Washington, D.C.",
    country: "United States",
    external_ref: "",
  },
];

/**
 * The sample file, built from the same column list and quoting rules as an
 * export - so what someone downloads to copy is exactly what {@link
 * parseMemberCsv} reads back, and cannot drift from it.
 */
export function sampleMemberCsv(): string {
  const lines = [
    CSV_COLUMNS.join(","),
    ...SAMPLE_ROWS.map((row) => CSV_COLUMNS.map((column) => escapeCell(row[column])).join(",")),
  ];

  return `${lines.join("\r\n")}\r\n`;
}
