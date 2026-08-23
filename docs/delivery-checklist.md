# Delivery Checklist

[← Index](README.md)

> **Note:** This file is *derived* from the assignment brief — it is not part of the source
> document. It flattens the requirements into a single tickable list.
>
> Unmarked items are the brief's mandatory scope. Items marked **`EXT`** come from
> [Campaign Data Model](campaign-data-model.md) and are tiered: **`EXT·2`** is cheap
> structure worth doing, **`EXT·3`** only with genuine time left. Ship every unmarked item
> before starting any `EXT` one.

## Core flow (must work end to end)

- [ ] Dashboard lists all campaigns
- [ ] Create campaign → saves to database
- [ ] Preview campaign as a customer
- [ ] Click a response option → event recorded
- [ ] Analytics view reflects the recorded event

## Dashboard

- [ ] Campaign name
- [ ] Status badge (Draft / Published)
- [ ] Date created
- [ ] View count
- [ ] Interaction count
- [ ] Preview action
- [ ] Edit action
- [ ] Create Campaign action
- [ ] Empty state
- [ ] `EXT·2` Objective shown on the card
- [ ] `EXT·2` Effective status badge (Draft / Scheduled / Active / Paused / Completed)
- [ ] `EXT·2` Schedule window shown
- [ ] `EXT·2` Recipient count shown
- [ ] `EXT·2` Compliance chip when a special category is set
- [ ] `EXT·2` Objective-driven primary metric leads the card
- [ ] `EXT·3` Status / objective filters and name search
- [ ] `EXT·3` Archived campaigns hidden by default

## Builder

- [ ] Campaign name field
- [ ] Video URL field
- [ ] Customer name field
- [ ] Personalised message field with `{{customer_name}}` support
- [ ] Option 1: label + follow-up response
- [ ] Option 2: label + follow-up response
- [ ] Campaign status control
- [ ] Save as Draft action
- [ ] Publish action
- [ ] Required-field validation with helpful messages
- [ ] Editing an existing campaign works
- [ ] `EXT·2` Objective selector (immutable after publish)
- [ ] `EXT·2` Start / end / timezone fields
- [ ] `EXT·2` Special category + conditional disclaimer field
- [ ] `EXT·2` Per-option intent (Positive / Negative / Neutral)
- [ ] `EXT·2` Follow-up type toggle: message **or** URL
- [ ] `EXT·2` Draft saves with only a name; Publish enforces the full contract
- [ ] `EXT·2` Publish failure marks **every** unmet field at once, not one per attempt
- [ ] `EXT·2` Unpublish blocked once events exist
- [ ] `EXT·3` Budget type / amount / spend cap
- [ ] `EXT·3` Send caps, pacing, frequency cap
- [ ] `EXT·3` UTM + external reference fields
- [ ] `EXT·3` Poster URL, headline, captions URL
- [ ] `EXT·3` Multi-recipient list / CSV upload

## Preview

- [ ] Video plays
- [ ] `{{customer_name}}` resolved in the message
- [ ] Customer name shown
- [ ] Two response buttons
- [ ] Response click hits the backend
- [ ] Follow-up message / destination shown
- [ ] Duplicate events prevented within a session
- [ ] `EXT·2` Compliance disclaimer rendered when a special category is set
- [ ] `EXT·2` Non-active campaigns blocked with `403 CAMPAIGN_NOT_LIVE`
- [ ] `EXT·2` Missing customer name falls back to `there`
- [ ] `EXT·2` Resolved values HTML-escaped on render
- [ ] `EXT·3` Recipient selector for multi-recipient campaigns
- [ ] `EXT·3` UTM params appended to follow-up URLs

## Analytics

- [ ] Total views
- [ ] Total interactions
- [ ] Interaction rate
- [ ] Option 1 clicks
- [ ] Option 2 clicks
- [ ] Percentage split
- [ ] *(Optional)* Chart or visual comparison
- [ ] Interaction rate is `0` when views is `0` — no `NaN`, no divide-by-zero
- [ ] Zero-click options still return a row
- [ ] `EXT·2` Objective-driven primary metric
- [ ] `EXT·3` Unique viewers
- [ ] `EXT·3` First / last activity timestamps
- [ ] `EXT·3` Daily timeseries

## Backend

- [ ] Create campaign
- [ ] List campaigns
- [ ] Get campaign
- [ ] Update campaign
- [ ] Record view
- [ ] Record response
- [ ] Get analytics
- [ ] Input validation and sanitisation
- [ ] Correct HTTP methods and status codes
- [ ] Consistent error response shape
- [ ] Routing / business logic / persistence separated
- [ ] Malformed and duplicate event protection
- [ ] Real database (not in-memory)
- [ ] Options stored as **rows**, not `option_1_*` / `option_2_*` columns
- [ ] Recipients stored as **rows**; the single-customer case is a one-row list
- [ ] Partial unique indexes enforce event dedup at the database level
- [ ] Duplicate event returns `200` + `"deduplicated": true`, not `409`
- [ ] `details` is always an array in the error envelope
- [ ] URLs restricted to `https` with a public hostname (SSRF)
- [ ] `occurred_at` from the server clock, not the client
- [ ] Raw IPs never stored — salted hash only
- [ ] `EXT·2` `effective_status` computed on read; no scheduler process
- [ ] `EXT·2` Status change is its own action route, not a `PATCH` field
- [ ] `EXT·2` State machine rejects illegal transitions with `409`
- [ ] `EXT·2` Objective frozen after publish
- [ ] `EXT·2` Stable option `key` survives label edits
- [ ] `EXT·3` Duplicate campaign endpoint
- [ ] `EXT·3` Archive (soft delete) endpoint
- [ ] `EXT·3` Recipient management endpoints
- [ ] `EXT·3` Resolved-preview endpoint
- [ ] `EXT·3` Money stored as integer minor units + currency

## Frontend quality

- [ ] Responsive on desktop and mobile
- [ ] Consistent spacing, typography, colours
- [ ] Reusable components
- [ ] Loading states
- [ ] Empty states
- [ ] Success states
- [ ] Error states
- [ ] Keyboard-friendly controls
- [ ] Readable contrast

## Submission

- [ ] Repository or ZIP
- [ ] README: install & run (frontend, backend, database)
- [ ] README: environment variables (example values only)
- [ ] README: technology choices and rationale
- [ ] README: API summary and data model
- [ ] README: features completed / not completed
- [ ] README: known limitations and next steps
- [ ] README: states what is *designed but not built* — send execution, multi-tenancy,
      auth, A/B experiences, scheduler
- [ ] README: AI tools disclosure
- [ ] Screen recording of the full flow
- [ ] Total time spent stated
- [ ] Live demo link *(if deployed)*
- [ ] No credentials or proprietary code committed
