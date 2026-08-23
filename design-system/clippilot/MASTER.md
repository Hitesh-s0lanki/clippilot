# ClipPilot — Design System (MASTER)

Global source of truth for interface decisions. A file in `pages/<route>.md` overrides this
for that route only; everything unstated here falls back to shadcn defaults.

**Provenance.** Token values are the ones already shipped in
[`frontend/src/app/globals.css`](../../frontend/src/app/globals.css) — this doc records and
verifies them, it does not replace them. UX rules marked `[db]` come from the
`ui-ux-pro-max` guideline database. Rules marked `[fallback]` are general defaults, not a
database match. The skill's whole-system generator was run twice and rejected both times
(it proposed a pink/Fira-Code system and an OLED-dark system, neither of which fits a
financial-services campaign console) — do not re-import its palette.

---

## 1. Foundations

Colour, radius, and font tokens live in `globals.css` and are addressed only through the
shadcn utilities (`bg-card`, `text-muted-foreground`, `border-border`). **No component
hardcodes a colour.**

### Verified contrast (WCAG 2.1)

Measured from the oklch token values, both themes. All text pairs clear AA (4.5:1):

| Pair | Light | Dark |
| --- | --- | --- |
| `foreground` on `background` | 16.98:1 | 17.41:1 |
| `muted-foreground` on `card` | 5.51:1 | 7.17:1 |
| `primary` on `card` | 5.82:1 | 5.98:1 |
| `primary-foreground` on `primary` | 5.65:1 | 6.43:1 |
| `destructive` / `success` / `warning` on `card` | 5.12 / 5.19 / 4.98:1 | 6.18 / 8.49 / 9.40:1 |
| `ring` on `background` (focus, needs 3:1) | 5.57:1 | 6.47:1 |

`muted-foreground` is safe for body copy — it is not the usual gray-on-gray failure.

### Resolved — `--input` now clears WCAG 1.4.11

`--input` is the border of every text field in the builder. It measured **1.27:1 (light)**
and **1.40:1 (dark)** against `card`; non-text UI boundaries need **3:1**. Applied with the
builder:

```css
:root { --input: oklch(0.65 0.012 265); } /* 3.24:1 */
.dark { --input: oklch(0.52 0.02 266); }  /* 3.23:1 */
```

Tradeoff accepted: a visibly heavier field border than stock shadcn. `--border`
(decorative separators, card edges) is exempt and stays as-is.

The dark value also drives `dark:bg-input/30` on inputs and `dark:hover:bg-input/50` on
outline buttons. Re-measured on those composites: `foreground` reads 11.9:1 and 9.3:1,
`muted-foreground` (placeholders) 5.3:1 — all still past AA.

### Spacing & density

Console density, not marketing density. Tailwind steps `2 / 3 / 4 / 6 / 8 / 12` for
in-page rhythm; `py-12` page padding; `max-w-5xl` content column (already the convention in
[`page.tsx`](../../frontend/src/app/page.tsx) and the dashboard). The customer preview is
the exception — see §4.3.

---

## 2. Semantic status colour

The lifecycle has five states plus a derived `INCOMPLETE`. Colour alone must never carry
the meaning `[db, High]` — every badge pairs a token with its own text.

| `effective_status` | Badge token | Reads as |
| --- | --- | --- |
| `DRAFT` | `secondary` | Draft |
| `DRAFT` + incomplete | `warning` | Draft · Incomplete |
| `SCHEDULED` | `primary` outline | Scheduled |
| `ACTIVE` | `success` | Active |
| `PAUSED` | `warning` | Paused |
| `COMPLETED` | `muted` | Completed |

Response intent: `POSITIVE` → `success`, `NEGATIVE` → `muted-foreground`, `NEUTRAL` →
`secondary`. Never red for `NEGATIVE` — "Not interested" is a valid outcome, not an error.

The compliance chip (`special_category ≠ NONE`) is an outline badge, never a filled alarm
colour. It is a disclosure, not a warning.

---

## 3. Verified UX rules

Severity as reported by the guideline database.

| Rule | Severity | Applies to |
| --- | --- | --- |
| Inputs need real `<label>`s — placeholder-only fails `[db]` | High | Builder |
| Errors announced via `role="alert"` / `aria-live`, not red border alone `[db]` | High | Builder |
| Submit shows loading → success/error; never a dead click `[db]` | High | Builder, Preview |
| Skeleton or spinner for any wait > 300ms `[db]` | High | All |
| `"use client"` only on the leaf that needs it `[db]` | High | All |
| Validate + authorise inside every Server Action `[db]` | High | Builder |
| Validate on blur, not on submit only `[db]` | Medium | Builder |
| Empty state = message + the action that fixes it `[db]` | Medium | Dashboard |
| Active nav item visually marked `[db]` | Medium | Chrome |
| URL reflects state (filters, selected recipient) for sharing `[db]` | Medium | Dashboard, Preview |
| Tables: `overflow-x-auto` wrapper or card layout on mobile `[db]` | Medium | Dashboard |
| No autoplay — click-to-play, `playsInline muted preload="none"` `[db]` | Medium | Preview |
| `Suspense` boundaries stream slow data instead of blocking `[db]` | Medium | Dashboard, Analytics |
| shadcn `asChild` for composition, not wrapper divs `[db]` | Medium | All |
| Transitions 150–300ms; `prefers-reduced-motion` already handled globally | — | All |

---

## 4. Screen briefs

### 4.1 Dashboard — campaign list

Card grid, not a dense table: each row carries a status badge, a schedule window, a
compliance chip and two metrics, which a table column set handles badly on mobile.

- **Lead metric is chosen by `objective`** — `AWARENESS` leads with views, everything else
  with the interaction rate. Views/interactions stay as secondary counts, minus whichever
  one the lead already shows.
- Primary action `Create campaign` top-right, present in the empty state too.
- **Empty state**: two of them. "No campaigns yet" offers the create button; "nothing
  matches these filters" offers to clear them. One message for both sends half the people
  who see it the wrong way.
- Status filter and name search write to the URL as query params.
- Card actions: `Preview` and `Edit`, plus an overflow menu offering only the transitions
  the current status allows. Icon-only buttons need `aria-label` `[db]`.

**As built, two deviations from this brief.** `GET /campaigns` returns
`CampaignListItem`, which carries neither the schedule window nor `metrics.primary_metric`
— so the card shows `created_at` (which the brief requires anyway) instead of the window,
and derives its lead metric from the objective plus the two counts it does receive. The
endpoint also has no `objective` filter, so the dashboard filters on status and name only
rather than shipping a client-side filter that would disagree with the pagination.

### 4.2 Builder — campaign form

Eight sections (Campaign, Schedule, Audience, Experience, Responses, Compliance, Budget,
Tracking) as an accordion, Tier 1 sections open by default. Progressive disclosure —
showing 40 fields at once is the anti-pattern.

- **Two actions, different contracts**: `Save as draft` needs only a name; `Publish` runs
  the full contract.
- **Publish stays enabled.** On failure it marks *every* unmet field inline at once and
  moves focus to the first one. A disabled button with no explanation is the worse failure.
- The `{{customer_name}}` field gets a live resolved preview beneath it, so the variable is
  understood without reading docs.
- Unpublish blocked once events exist — the API answers `409 CAMPAIGN_LOCKED` and its
  message is surfaced as-is. There is no duplicate endpoint to offer instead, so the menu
  does not promise one.
- Every field carries a dotted path (`experience.options.1.label`) that is also its DOM id,
  so an API error and a client rule address the same field by the same string, and a
  rejected publish can open the section holding the first one and focus it.

### 4.3 Preview — the customer view

The only screen that is not console chrome. Single centred column, `max-w-2xl`, no app
nav — the customer is not a user of the product.

- Click-to-play video, `playsInline preload="none"` `[db]`. Poster image reserves the
  aspect box so nothing shifts (CLS) `[db]`. **`muted` is deliberately not set**: it exists
  to make autoplay permissible, and there is no autoplay here — muting a personalised video
  pitch would remove the pitch.
- Resolved message above the video; the two options as large, equal-weight buttons —
  **not** primary vs. ghost. Weighting them biases the response and corrupts the metric.
- Minimum 44×44px targets, 8px+ apart `[fallback — standard touch guidance]`.
- After a click: buttons disable, the follow-up renders, and the `session_id` guard
  prevents a second event. A URL follow-up is offered as a `Continue` button with its
  destination shown, not an automatic redirect — being thrown to another site mid-read
  takes the confirmation away before it can be read.
- The owner's own preview renders the identical component in `owner` mode: follow-ups are
  resolved locally with the same substitution rules and **nothing is recorded**, so
  checking a draft cannot pollute its own analytics.
- Disclaimer beneath the video whenever a special category is declared.

### 4.4 Analytics

Objective-driven headline number, large, with the brief's six metrics as a supporting row.

- **Chart: a single horizontal 100% stacked bar** for the option split, with value labels
  and a legend. The database explicitly flags pie/donut as `⚠ hard for accessibility` and
  recommends a stacked bar with legend instead `[db]`.
- Two categories do not need a charting library — an SVG or flex bar using `--chart-1` /
  `--chart-2` is enough, and `recharts` is not currently a dependency.
- Every option renders a row **including zero-click ones**; `interaction_rate` is `0` when
  views are `0` — never `NaN`.
- Percentages always accompanied by the raw count.

---

## 5. Icons

`lucide-react` (already a dependency). **No emoji as icons.** Verified matches:
`BarChart` (analytics), `Play` / `Pause` (video), `Video` (campaign media),
`PieChart` (split). Decorative icons take `aria-hidden="true"`; icon-only buttons take a
real `aria-label`.

---

## 6. Pre-delivery checklist

- [ ] No emoji icons — SVG (Lucide) only
- [ ] `cursor-pointer` on every clickable element
- [ ] Hover + focus-visible states, 150–300ms transitions
- [ ] Text contrast ≥ 4.5:1 in both themes
- [ ] Focus ring visible and never removed
- [ ] `prefers-reduced-motion` respected (global rule already in `globals.css`)
- [ ] Responsive at 375 / 768 / 1024 / 1440px, no horizontal scroll
- [ ] Loading, empty, success and error state for every async surface
- [ ] Keyboard path through builder and preview, start to finish
