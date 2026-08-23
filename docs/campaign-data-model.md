# Campaign Data Model

[← Index](README.md) · Related: [Functional Requirements](03-functional-requirements.md) · [Backend Requirements](04-backend-requirements.md)

> **Note:** This file is *derived* — it is **not** part of the source assignment document.
> The brief describes a campaign as a video URL, one message and two buttons. That is a
> *creative*, not a campaign. This document promotes **Campaign** to a proper top-level
> entity modelled on the [Meta Marketing API campaign object](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group/),
> and nests the ads beneath it.
>
> Everything the brief mandates is preserved and marked **`BRIEF`**. Everything added here
> is marked **`EXT`** — a deliberate extension, not a misreading of the scope. See
> [§8 Scope guidance](#8-scope-guidance) for what to build first if time runs short.

---

## 1. Why the campaign is the top level

In Meta Ads the hierarchy is three tiers, and each tier owns a distinct concern:

| Meta tier | Owns | Trustvid equivalent |
| --- | --- | --- |
| **Campaign** | Objective, status, budget ceiling, compliance category | **Campaign** — this document |
| **Ad Set** | Audience, schedule, delivery pacing, budget | Folded **into Campaign** |
| **Ad** | Creative — video, copy, call to action | **Ad** — nested child, 1:N |

Trustvid campaigns are **sent to a known recipient list**, not bid into an auction, so the
ad-set tier carries no independent meaning: one campaign has one audience and one schedule.
Collapsing it keeps a single builder screen and a single analytics roll-up while still
giving the campaign every field a real top-level campaign carries.

```
Campaign  (top level — owns objective, lifecycle, schedule, budget, audience, compliance)
│
├── Ads[]  (1:N — each one a creative: video + copy + CTA + options, with its own status)
│   └── Options[2]  (label + follow-up)
│
└── Audience  (N:1 — a reusable list, referenced not owned)
    └── Members[]  (the people)
│
└── Events[]  (views + responses → analytics)
```

**Design decision:** a campaign owns **many ads**. `campaign_ads` is a separate table with a
`campaign_id` foreign key, so an A/B variant is an insert. Each ad carries its own `status`,
which is what makes pausing one creative without touching the rest of the campaign possible —
and what makes `AdEffectiveStatus.CAMPAIGN_PAUSED` necessary: an ad can be switched on,
complete, and still delivering nothing because the level above it is not running.

---

## 2. Campaign entity

### 2.1 Identity

| Field | Type | Req. | Source | Notes |
| --- | --- | :---: | :---: | --- |
| `id` | UUID | auto | `EXT` | Server-generated. Never reuse. |
| `name` | string(1–120) | ✅ | `BRIEF` | Unique per workspace. Trimmed, collapsed whitespace. |
| `description` | string(0–500) | — | `EXT` | Internal note. Never shown to the recipient. |
| `objective` | enum | ✅ | `EXT` | See [§2.2](#22-objective). Immutable once published. |
| `created_at` | timestamptz | auto | `BRIEF` | Dashboard "Date created". |
| `updated_at` | timestamptz | auto | `EXT` | Bumped on any write. |
| `published_at` | timestamptz | — | `EXT` | Set on the first `DRAFT → SCHEDULED/ACTIVE` transition. |
| `archived_at` | timestamptz | — | `EXT` | Set on archive. Archived campaigns are hidden by default. |

> Multi-tenancy is [explicitly out of scope](04-backend-requirements.md#explicitly-not-required),
> so there is no `workspace_id`. Add it as the first column of every table when it lands.

### 2.2 Objective

`EXT` — Meta requires an objective before anything else, because it decides what
"performing well" means. Trustvid's analytics view uses it the same way: the objective
picks the **primary metric** shown large at the top of [§7 Analytics](#7-analytics-contract).

| Value | Campaign is for | Primary metric |
| --- | --- | --- |
| `AWARENESS` | Getting the message seen | Total views |
| `ENGAGEMENT` | Getting any response *(default)* | Interaction rate |
| `LEAD_CAPTURE` | Getting positive intent | Positive-option click rate |
| `CONVERSION` | Driving through to a destination | Follow-up URL click-through |
| `RETENTION` | Re-engaging existing customers | Repeat-view rate |

The illustrative brief campaign — *"Hi Rahul, we have identified an investment opportunity
for you"* with **Tell me more** / **Not interested** — is `LEAD_CAPTURE`.

### 2.3 Status and lifecycle

`BRIEF` mandates `Draft` / `Published`. That contract is preserved: the dashboard badge
still reads Draft or Published. `EXT` splits Published into the states a real campaign
actually moves through, because "published but its start date is next Monday" and
"published and finished last week" are not the same thing to a campaign manager.

Two fields, mirroring Meta's `configured_status` / `effective_status` split:

| Field | Type | Written by | Notes |
| --- | --- | --- | --- |
| `status` | enum | The user | What the user chose. Persisted. |
| `effective_status` | enum | The server | Derived from `status` + schedule + completeness. **Read-only.** |

**`status` values**

| Value | Meaning | Recipient can view? |
| --- | --- | :---: |
| `DRAFT` | Being configured. May be incomplete. | ❌ |
| `SCHEDULED` | Complete and published, `start_at` is in the future. | ❌ |
| `ACTIVE` | Live and inside its schedule window. | ✅ |
| `PAUSED` | Manually halted. Resumable. | ❌ |
| `COMPLETED` | Past `end_at`. Terminal for delivery; analytics stay readable. | ❌ |
| `ARCHIVED` | Hidden from the dashboard. Terminal. | ❌ |

**`effective_status`** adds one value the user cannot set:

| Value | When |
| --- | --- |
| `INCOMPLETE` | `status = DRAFT` **and** the publish contract in [§4](#4-validation-contract) is unmet. |

**Brief-compatible badge** — the dashboard derives it, so the brief's contract holds:

```
Draft      ⟵  status ∈ { DRAFT }
Published  ⟵  status ∈ { SCHEDULED, ACTIVE, PAUSED, COMPLETED }
```

**State machine**

```
                    ┌──────────── archive ────────────┐
                    │                                 ▼
  ┌───────┐ publish ┌───────────┐ start_at  ┌────────┐ end_at  ┌───────────┐  ┌──────────┐
  │ DRAFT │────────▶│ SCHEDULED │──────────▶│ ACTIVE │────────▶│ COMPLETED │─▶│ ARCHIVED │
  └───────┘         └───────────┘  reached  └────────┘ reached └───────────┘  └──────────┘
      ▲                   │                   │    ▲                               ▲
      │                   │      pause        │    │ resume                        │
      │                   └───────────────────┼────┼──▶ ┌────────┐ ────────────────┘
      │                                       └────┴─── │ PAUSED │      archive
      └────────────── unpublish (no events yet) ─────── └────────┘
```

**Transition rules**

- `DRAFT → SCHEDULED|ACTIVE` requires the full publish contract ([§4](#4-validation-contract)).
  The server picks `ACTIVE` when `start_at` is null or already passed, `SCHEDULED` otherwise.
- `SCHEDULED → ACTIVE` and `ACTIVE → COMPLETED` are **time-driven**, evaluated on read.
  No scheduler process is required — `effective_status` is computed per request.
- **Unpublish** back to `DRAFT` is allowed **only while the campaign has zero events**.
  Once a real customer has seen it, its content is frozen against silent rewriting.
- `ARCHIVED` and `COMPLETED` are terminal. Duplicate a campaign to run it again.
- Any transition to a state that is not reachable → `409 CAMPAIGN_INVALID_TRANSITION`.

### 2.4 Schedule

`EXT` — Meta carries schedule on the ad set. Flattened here.

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `start_at` | timestamptz | — | Null = live the moment it is published. |
| `end_at` | timestamptz | — | Null = runs until manually paused. |
| `timezone` | IANA string | ✅ | Default `UTC`. Display timezone for the builder and analytics. |

**Rules** — `end_at` must be strictly after `start_at`; `start_at` may not move into the
past once published; editing `end_at` on a `COMPLETED` campaign reopens it to `ACTIVE`.

### 2.5 Budget and delivery

`EXT` — Meta's `daily_budget` / `lifetime_budget` / `spend_cap` / `pacing_type`.

A video journey has two distinct costs, so both are modelled. **Money is optional; volume
is the one that actually governs delivery.**

**Money** *(nullable — many campaigns have no media spend)*

| Field | Type | Notes |
| --- | --- | --- |
| `budget_type` | enum | `NONE` *(default)* \| `DAILY` \| `LIFETIME` |
| `budget_amount_minor` | integer | **Minor units** (paise, cents). Never a float. Required unless `budget_type = NONE`. |
| `currency` | ISO 4217 | Default `INR`. Immutable once any spend is recorded. |
| `spend_cap_minor` | integer | Hard ceiling across the campaign's life. Must be ≥ `budget_amount_minor`. |

**Volume**

| Field | Type | Notes |
| --- | --- | --- |
| `send_cap_total` | integer | Max sends over the campaign's life. Null = uncapped. |
| `send_cap_per_day` | integer | Max sends per calendar day in `timezone`. Null = uncapped. |
| `frequency_cap_per_recipient` | integer | Max sends to one recipient. Default `1`. |
| `pacing` | enum | `STANDARD` — spread evenly across the window *(default)*. `ACCELERATED` — send as fast as possible. |

> `ACCELERATED` with no `end_at` is rejected: there is no window to accelerate through.

### 2.6 Compliance category

`EXT` — Meta's `special_ad_categories`, and **not decorative here**: the brief's own
illustrative campaign is a financial-services company pitching an investment opportunity,
which is precisely the case Meta forces a declared category and a disclaimer on.

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `special_category` | enum | ✅ | `NONE` *(default)* \| `FINANCIAL_PRODUCTS_SERVICES` \| `CREDIT` \| `EMPLOYMENT` \| `HOUSING` |
| `disclaimer_text` | string(0–500) | conditional | **Required when `special_category ≠ NONE`.** Rendered beneath the video on the preview page. |

Default copy offered by the builder for `FINANCIAL_PRODUCTS_SERVICES`:

```text
Investments are subject to market risk. Read all scheme-related documents carefully.
This is not investment advice.
```

### 2.7 Tracking

`EXT` — so follow-up destination clicks are attributable in the customer's own analytics.

| Field | Type | Notes |
| --- | --- | --- |
| `utm_source` | string(0–80) | Default `trustvid` |
| `utm_medium` | string(0–80) | Default `interactive-video` |
| `utm_campaign` | string(0–80) | Defaults to a slug of `name` |
| `utm_content` | string(0–80) | Defaults to the clicked option's `key` |
| `external_ref` | string(0–120) | CRM / campaign-tool id. Indexed. Unique when present. |

Non-empty UTM params are appended to any `follow_up_url` at click time. Params already
present on the destination URL win — Trustvid never overwrites an explicit value.

---

## 3. Nested entities

### 3.1 Ad (the creative)

Up to **five** per campaign — `MAX_ADS_PER_CAMPAIGN`. Each one is what a recipient actually
watches.

Five, not twenty: a campaign is a single message tested a few ways, and a list long enough
to need scrolling is a list nobody compares.

**The campaign is created first, then its ads.** `POST /campaigns` accepts ads inline, but
the builder deliberately does not send them — it saves the campaign and takes the user to
its ads screen. Asking someone to invent a creative before the campaign it belongs to
exists is what made the old single form long enough to lose people in.

| Field | Type | Req. | Source | Notes |
| --- | --- | :---: | :---: | --- |
| `id` | UUID | auto | `EXT` | |
| `campaign_id` | UUID | ✅ | `EXT` | FK → `campaigns.id`, `ON DELETE CASCADE`. |
| `name` | string(1–120) | ✅ | `EXT` | Internal label, unique per campaign (case-insensitive). Never shown to a recipient. |
| `status` | enum | ✅ | `EXT` | `DRAFT` *(default)* \| `ACTIVE` \| `PAUSED` \| `ARCHIVED`. Independent of the campaign's. |
| `video_url` | URL | ✅ | `BRIEF` | Publicly accessible. `https` only. `.mp4` / `.webm` / `.mov`. |
| `poster_url` | URL | — | `EXT` | Thumbnail before playback. Also the dashboard card image. |
| `captions_url` | URL | — | `EXT` | WebVTT. Accessibility — see [§8](#8-scope-guidance). |
| `video_duration_seconds` | integer | — | `EXT` | Metadata only. No processing is performed. |
| `headline` | string(0–80) | — | `EXT` | Shown above the video. Supports variables. |
| `description` | string(0–500) | — | `EXT` | Supporting line beneath the headline. **Recipient-facing**, unlike `campaigns.description`, which is an internal note. |
| `personalised_message` | string(1–500) | ✅ | `BRIEF` | Supports variables. See [§3.3](#33-personalisation-variables). |
| `cta` | enum | ✅ | `EXT` | `LEARN_MORE` *(default)*, `BOOK_NOW`, `GET_QUOTE`, `SIGN_UP`, … Names the POSITIVE option's intent and supplies its default label. |

**Derived: `effective_status`.** Mirrors the campaign's `status` / `effective_status` split
one level down.

| Value | Means |
| --- | --- |
| `INCOMPLETE` | Missing a video, a message, or two valid options |
| `DRAFT` | Finished, not switched on yet |
| `ACTIVE` | Switched on, complete, and its campaign is live — the only value a recipient can open |
| `PAUSED` | Switched off deliberately |
| `CAMPAIGN_PAUSED` | Switched on and faultless, but the campaign above it is not running |
| `ARCHIVED` | Terminal |

**Why the CTA is an enum and not a second button.** The two response options already *are*
the calls to action. `cta` names what the positive one asks for and fills in its label when
the user has not written one, so choosing "Book now" is not also a copywriting task. The
two-button interaction is unchanged.

### 3.2 Option

Exactly **two** per ad, `position` 1 and 2 — `BRIEF`. Stored as rows, not columns, so a
third option is data rather than a schema change.

| Field | Type | Req. | Source | Notes |
| --- | --- | :---: | :---: | --- |
| `id` | UUID | auto | `EXT` | |
| `ad_id` | UUID | ✅ | `EXT` | FK → `campaign_ads.id`, cascade. |
| `position` | smallint | ✅ | `BRIEF` | `1` or `2`. Unique per ad. |
| `key` | slug | auto | `EXT` | Stable analytics key, slug of `label` at creation. Never changes when the label is reworded. |
| `label` | string(1–40) | ✅ | `BRIEF` | Button text. e.g. `Tell me more`. Defaults from the ad's `cta` when left blank. |
| `intent` | enum | ✅ | `EXT` | `POSITIVE` \| `NEGATIVE` \| `NEUTRAL`. Feeds the `LEAD_CAPTURE` primary metric. |
| `follow_up_type` | enum | ✅ | `EXT` | `MESSAGE` *(default)* \| `URL` |
| `follow_up_message` | string(1–500) | conditional | `BRIEF` | Required when `follow_up_type = MESSAGE`. Supports variables. |
| `follow_up_url` | URL | conditional | `BRIEF` | Required when `follow_up_type = URL`. `https` only. Gets UTM params appended. |

> `key` exists because a campaign manager rewording *"Tell me more"* to *"Yes, I'm
> interested"* must not split the metric into two series. Meta solves this with immutable
> object ids; this is the same idea at option level.

### 3.3 Personalisation variables

`BRIEF` mandates `{{customer_name}}`. `EXT` generalises the resolver — the same
substitution runs over `headline`, `personalised_message` and `follow_up_message`.

| Variable | Resolves to | Source |
| --- | --- | :---: |
| `{{customer_name}}` | `audience_member.full_name` | `BRIEF` |
| `{{first_name}}` | The leading word of `full_name` | `EXT` |
| `{{city}}` | `audience_member.city` | `EXT` |
| `{{country}}` | `audience_member.country` | `EXT` |
| `{{campaign_name}}` | `campaign.name` | `EXT` |
| `{{option_label}}` | The clicked option's label *(follow-up copy only)* | `EXT` |

`{{first_name}}` exists because "Hi Rahul" reads like a person wrote it and "Hi Rahul
Mehta" does not, which is the whole reason a campaign personalises at all.

**Resolution rules**

- Unknown variable → left **literal** and surfaced as a builder warning. Never blanked
  silently, and never a 500.
- No member named on the link → falls back to the audience's first member; with no audience,
  to `there` (`Hi there, …`), so a preview is never broken. The preview and the follow-up
  resolve identically, so the two halves of one interaction cannot disagree about who is watching.
- Missing `city` or `country` → falls back to `your city` / `your country`. A place has no
  neutral word the way a name has `there`, but it needs one all the same: rendering `""`
  turns "an opportunity in {{city}}" into "an opportunity in ." for every member whose city
  was never filled in — and a ragged list is the normal case, not an edge.
- Resolved values are **HTML-escaped** at render. A customer name is untrusted input.
- Whitespace inside the braces is tolerated: `{{ customer_name }}` resolves.

### 3.4 Audience and its members

`BRIEF` carries a single `customer_name` on the campaign. `EXT` promotes the audience to a
**top-level, reusable entity**: a list is built once — by hand or from a
[CSV upload](07-scope-and-enhancements.md#72-optional-enhancements) — and any number of
campaigns select it. The brief's single-customer case is an audience of one.

A campaign therefore holds a **reference**, not a copy. `campaigns.audience_id` is
`ON DELETE SET NULL`: deleting a list must never delete the campaigns that used it or their
analytics, so the campaign simply falls back to unpublishable until another list is chosen.

**`audiences`**

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `id` | UUID | auto | |
| `owner_user_id` | string(120) | ✅ | Clerk user id. No local users table. |
| `name` | string(1–120) | ✅ | Unique per owner, case-insensitive. |
| `description` | string(0–500) | — | Internal note. |
| `member_count` | integer | auto | Denormalised, recomputed from a `COUNT` after every membership change. Two reads need it where a query cannot run: the listing (an N+1 otherwise) and `collect_publish_blockers`, which is synchronous. |

**`audience_members`**

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `id` | UUID | auto | |
| `audience_id` | UUID | ✅ | FK, cascade. |
| `full_name` | string(1–80) | ✅ | `BRIEF`. Resolves `{{customer_name}}`. The only required field — a real uploaded list is ragged. |
| `email` | email | — | Unique per audience when present, case-insensitively. |
| `phone` | E.164 | — | |
| `age` | integer | — | The number, never the bucket: a stored bucket is wrong the morning after a birthday. |
| `gender` | enum | ✅ | `FEMALE` \| `MALE` \| `OTHER` \| `UNKNOWN` *(default)*. `UNKNOWN` is a real bucket, not a null — a breakdown has to account for everyone. |
| `city` / `country` | string | — | Normalised on write so `USA` and `United States` do not become two segments. |
| `external_ref` | string(0–120) | — | CRM contact id. |
| `attributes` | JSON | — | Free-form, carried through import and export untouched. |
| `created_at` | timestamptz | auto | |

`age_group` is **derived at read time** from `age`, never stored.

**Sample data.** An account with no audiences is given three sample lists — 100 people in
total — on its first listing, so every user lands on a populated segment breakdown instead
of an empty screen. Each account gets its **own copy**, not a shared row: a global list
would let one user edit or delete what every other user targets, and a campaign can only
reference an audience its owner holds. The provisioning is idempotent by name, so it never
doubles anybody, and `SAMPLE_AUDIENCES=false` turns it off for a tenant that should start
clean.

### 3.5 Event

| Field | Type | Req. | Notes |
| --- | --- | :---: | --- |
| `id` | UUID | auto | |
| `campaign_id` | UUID | ✅ | FK, cascade. Denormalised for fast analytics. |
| `ad_id` | UUID | — | FK → `campaign_ads.id`, `ON DELETE SET NULL` — deleting one creative must not erase the campaign's view history. |
| `member_id` | UUID | — | Null for anonymous preview traffic. |
| `session_id` | UUID | ✅ | Client-generated per preview session. The dedup key. |
| `type` | enum | ✅ | `VIEW` \| `RESPONSE` |
| `option_id` | UUID | conditional | Required when `type = RESPONSE`, must be null otherwise. |
| `occurred_at` | timestamptz | auto | Server clock. Client timestamps are not trusted. |
| `user_agent` | string(0–255) | — | Truncated. |
| `ip_hash` | char(64) | — | SHA-256 of IP + a server-side salt. **The raw IP is never stored.** |

**Duplicate protection** — `BRIEF` mandates it. Enforced in the database, not just the app:

```sql
-- One VIEW per session
CREATE UNIQUE INDEX uniq_view_per_session
  ON campaign_events (campaign_id, session_id)
  WHERE type = 'VIEW';

-- One RESPONSE per session, regardless of which option
CREATE UNIQUE INDEX uniq_response_per_session
  ON campaign_events (campaign_id, session_id)
  WHERE type = 'RESPONSE';
```

A duplicate returns **`200`** with the *original* event and `"deduplicated": true` — not a
`409`. A double-click is not a client error, and the preview page must not show a failure
state for one.

---

## 4. Validation contract

The central rule, and the reason `DRAFT` and `INCOMPLETE` are distinct: **a draft may be
incomplete; publishing enforces the full contract.** Meta works the same way — you can save
a half-built campaign, but not run one.

| Field | Required to save a `DRAFT` | Required to publish |
| --- | :---: | :---: |
| `name` | ✅ | ✅ |
| `objective` | — *(defaults `ENGAGEMENT`)* | ✅ |
| `timezone` | — *(defaults `UTC`)* | ✅ |
| `special_category` | — *(defaults `NONE`)* | ✅ |
| `disclaimer_text` | — | ✅ *when category ≠ `NONE`* |
| `ads` | — | ✅ at least one **complete** ad |
| `ads.{i}.video_url` | — | ✅ on that ad |
| `ads.{i}.personalised_message` | — | ✅ on that ad |
| Both options: `label` | — | ✅ |
| Both options: follow-up (message **or** url) | — | ✅ |
| an audience with ≥ 1 member | — | ✅ |
| `budget_amount_minor` | — | ✅ *when `budget_type ≠ NONE`* |

**Cross-field rules**

1. `end_at > start_at`.
2. `spend_cap_minor ≥ budget_amount_minor`.
3. `pacing = ACCELERATED` requires a non-null `end_at`.
4. `special_category ≠ NONE` requires non-empty `disclaimer_text`.
5. `follow_up_type = URL` requires `follow_up_url`; `MESSAGE` requires `follow_up_message`.
6. Exactly two options, at `position` 1 and 2.
8. `objective` is immutable once `published_at` is set — it would invalidate historical metrics.

**Sanitisation**

- All strings: trim, collapse internal whitespace runs, reject control characters.
- All URLs: `https` scheme only, hostname must resolve to a public address
  (blocks `localhost` / private ranges / SSRF).
- All rich text: HTML-escaped on output, never on input — storage keeps what the user typed.

**Failure shape** — one envelope for everything, matching
[`backend/README.md`](../backend/README.md#error-envelope):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The campaign cannot be published.",
    "details": [
      { "field": "ads.0.video_url", "code": "REQUIRED", "message": "A video URL is required before publishing." },
      { "field": "disclaimer_text",      "code": "REQUIRED_WHEN", "message": "A disclaimer is required for financial services campaigns." }
    ]
  }
}
```

`details` is **always an array**, even for a single error — the frontend maps it straight
onto field-level messages without branching on shape.

### Error codes

| Code | HTTP | When |
| --- | :---: | --- |
| `VALIDATION_ERROR` | 422 | Any field or cross-field rule fails |
| `CAMPAIGN_NOT_FOUND` | 404 | Unknown id, or archived and not explicitly requested |
| `CAMPAIGN_NAME_TAKEN` | 409 | Duplicate `name` |
| `CAMPAIGN_INVALID_TRANSITION` | 409 | Illegal `status` change |
| `CAMPAIGN_NOT_LIVE` | 403 | Preview requested while `effective_status ≠ ACTIVE` |
| `CAMPAIGN_LOCKED` | 409 | Unpublish or objective change attempted after events exist |
| `EVENT_INVALID_OPTION` | 422 | `option_id` does not belong to this campaign |

---

## 5. Wire format

`GET /api/v1/campaigns/{id}` — full read. `EXT` fields marked inline.

```json
{
  "id": "9f1c2b7a-3d4e-4a55-9c10-6f2e8b4d1a77",
  "name": "Investment Opportunity — Q3 HNI",
  "description": "Follow-up for customers who opened the July portfolio review.",
  "objective": "LEAD_CAPTURE",

  "status": "ACTIVE",
  "effective_status": "ACTIVE",
  "badge": "Published",

  "schedule": {
    "start_at": "2026-08-25T09:00:00Z",
    "end_at": "2026-09-25T18:30:00Z",
    "timezone": "Asia/Kolkata"
  },

  "budget": {
    "budget_type": "LIFETIME",
    "budget_amount_minor": 5000000,
    "currency": "INR",
    "spend_cap_minor": 6000000
  },

  "delivery": {
    "pacing": "STANDARD",
    "send_cap_total": 2500,
    "send_cap_per_day": 250,
    "frequency_cap_per_recipient": 1
  },

  "compliance": {
    "special_category": "FINANCIAL_PRODUCTS_SERVICES",
    "disclaimer_text": "Investments are subject to market risk. Read all scheme-related documents carefully."
  },

  "tracking": {
    "utm_source": "trustvid",
    "utm_medium": "interactive-video",
    "utm_campaign": "investment-opportunity-q3-hni",
    "utm_content": null,
    "external_ref": "CRM-88213"
  },

  "audience": { "id": "b2…", "name": "Lapsed SIP investors", "member_count": 1 },

  "ads": [{
    "id": "4e…",
    "campaign_id": "9f…",
    "name": "Advisor call — risk-matched",
    "status": "ACTIVE",
    "effective_status": "ACTIVE",
    "video_url": "https://cdn.example.com/investment-opportunity.mp4",
    "poster_url": "https://cdn.example.com/investment-opportunity.jpg",
    "captions_url": null,
    "video_duration_seconds": 42,
    "headline": "A moment of your time, {{customer_name}}",
    "description": "Reviewed by an advisor, matched to your risk profile.",
    "personalised_message": "Hi {{customer_name}}, we have identified an investment opportunity for you.",
    "cta": "LEARN_MORE",
    "blockers": [],
    "options": [
      {
        "id": "7a…", "position": 1, "key": "tell-me-more", "label": "Tell me more",
        "intent": "POSITIVE", "follow_up_type": "MESSAGE",
        "follow_up_message": "Great, {{customer_name}} — an advisor will call you within 24 hours.",
        "follow_up_url": null
      },
      {
        "id": "7b…", "position": 2, "key": "not-interested", "label": "Not interested",
        "intent": "NEGATIVE", "follow_up_type": "MESSAGE",
        "follow_up_message": "No problem. We won't follow up on this one.",
        "follow_up_url": null
      }
    ]
  },

  "metrics": {
    "views": 128, "interactions": 74, "interaction_rate": 0.578,
    "primary_metric": { "key": "positive_rate", "label": "Positive intent", "value": 0.365 },
    "last_activity_at": "2026-08-21T07:14:02Z"
  },

  "created_at": "2026-08-18T11:20:33Z",
  "updated_at": "2026-08-21T06:02:11Z",
  "published_at": "2026-08-19T04:00:00Z",
  "archived_at": null
}
```

**Conventions**

- `snake_case` keys; ISO-8601 UTC timestamps with a trailing `Z`.
- Enums are `SCREAMING_SNAKE_CASE` on the wire; the frontend owns the human labels.
- Money is **always integer minor units** plus an explicit currency. No floats.
- Rates are decimals in `0.0–1.0`, not pre-formatted percentages.
- `metrics` and `effective_status` / `badge` are **read-only** — sent on `GET`, ignored on write.

`GET /api/v1/campaigns` returns the same object minus `audience` (it carries
`audience_name` and `audience_size` instead),
`ads` and `description` — enough for the dashboard card, small enough to list. It carries
`ad_count` and `live_ad_count` instead.

---

## 6. Persistence sketch

Five tables. Every child cascades from `campaigns`, so deleting a campaign is one statement.

```
campaigns ──1:N──▶ campaign_ads ──1:N──▶ ad_options
    │                                                   ▲
    ├──N:1──▶ audiences ──1:N──▶ audience_members       │
    │                               │                   │
    └──1:N──▶ campaign_events ──────┴───────────────────┘
                (member_id, ad_id, option_id nullable FKs)
```

**Indexes that matter**

| Index | On | Why |
| --- | --- | --- |
| `uniq_campaign_name` | `campaigns (lower(name))` | `CAMPAIGN_NAME_TAKEN` at the DB, not a race-prone pre-check |
| `idx_campaign_status_created` | `campaigns (status, created_at DESC)` | Dashboard list + status filter |
| `uniq_view_per_session` | partial, `type='VIEW'` | Duplicate view protection |
| `uniq_response_per_session` | partial, `type='RESPONSE'` | Duplicate response protection |
| `idx_events_campaign_type` | `campaign_events (campaign_id, type)` | Analytics aggregation |
| `uniq_option_position` | `ad_options (ad_id, position)` | Exactly two options, no gaps |
| `uniq_ad_name_per_campaign` | `campaign_ads (campaign_id, lower(name))` | Ad names unique within their campaign |

**Deliberate choices**

- Options are **rows, not columns**. `option_1_label` / `option_2_label` columns would make
  a third option a migration and make analytics a `UNION`.
- `campaign_id` is denormalised onto `campaign_events` — analytics never joins through
  `campaign_ads` to count a view, and the count survives the ad being deleted.
- An ad with recorded activity cannot be deleted, only archived: its events carry the
  campaign's history, and deleting the creative they refer to leaves that history
  unexplainable.
- Money in `BIGINT` minor units. Never `FLOAT`.
- Enums as constrained `TEXT`, not native DB enums — adding a value stays a code change.
- All timestamps `timestamptz`. `timezone` is a **display** preference, never a storage format.

---

## 7. Analytics contract

`GET /api/v1/campaigns/{id}/analytics`

| Metric | Source | Notes |
| --- | --- | :---: |
| `views` | `count(events where type=VIEW)` | `BRIEF` |
| `interactions` | `count(events where type=RESPONSE)` | `BRIEF` |
| `interaction_rate` | `interactions / views` | `BRIEF`. `0` when `views = 0` — **never divide by zero.** |
| `by_option[]` | Per option: `key`, `label`, `intent`, `clicks`, `share` | `BRIEF` (clicks + split) |
| `primary_metric` | Chosen by `objective` — see [§2.2](#22-objective) | `EXT` |
| `unique_viewers` | `count(distinct session_id)` | `EXT` |
| `first_activity_at` / `last_activity_at` | Event range | `EXT` |
| `timeseries[]` | Daily `{ date, views, interactions }` in the campaign's `timezone` | `EXT` — feeds the optional chart |

`by_option` returns a **row for every option, including zero-click ones**. A chart with a
missing bar is a bug the frontend should not have to guess around. `share` sums to `1.0`
across options, or is `0` for all when there are no interactions.

---

## 8. Scope guidance

The [brief's priority](README.md#the-one-thing-that-matters-most) stands: a reliable core
flow beats broad partial features. Build in this order.

**Tier 1 — the brief. Ship this first, complete.**
`name` · `status` (Draft/Published) · `created_at` · `video_url` · `personalised_message`
with `{{customer_name}}` · an audience of one · two options with labels + follow-ups ·
view & response events with dedup · views / interactions / rate / split.

**Tier 2 — cheap structure, high signal.** Roughly an hour, and it is what makes the
model read as a real campaign rather than a form:
`objective` · the six-state `status` + derived `effective_status` + `badge` ·
`start_at` / `end_at` / `timezone` · `special_category` + `disclaimer_text` ·
option `key` + `intent` · options and audience members as **rows**.

> The row-based schema is the one Tier-2 item worth doing even if nothing else is —
> retrofitting it later touches every layer.

**Tier 3 — only with genuine time left.**
Money budget & spend cap · send caps & pacing · UTM tracking · `poster_url` /
`captions_url` / `headline` · reusable audiences & CSV upload · `timeseries` + chart.

**Documented as designed, not built** — say so plainly in the README rather than leaving it
ambiguous: multi-tenancy · authentication · real send/delivery execution (the caps in
[§2.5](#25-budget-and-delivery) are stored and validated, nothing dispatches) · A/B
scheduler process (schedule states are computed on read, not driven by a job).

---

[← Index](README.md) · [Functional Requirements](03-functional-requirements.md) · [Backend Requirements](04-backend-requirements.md) · [Delivery Checklist](delivery-checklist.md)
