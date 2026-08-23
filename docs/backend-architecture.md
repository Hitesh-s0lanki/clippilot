# Backend Architecture — Schemas, Services, Routing

[← Index](README.md) · Related: [Campaign Data Model](campaign-data-model.md) · [Backend Requirements](04-backend-requirements.md)

How a request flows, and what each layer owns.

```
HTTP request
    ↓
src/app/router.py          route registry — URL → controller
    ↓
src/controllers/           HTTP in / HTTP out. No business rules.
    ↓
src/app/dependencies.py    injects the Clerk user, a DB session and services
    ↓
src/services/              business logic. No FastAPI, no SQLAlchemy.
    ↓
src/repositories/          the only modules that build SQL
    ↓
src/models/                SQLAlchemy ORM — five tables
```

Each layer imports only downward. `services/` has no FastAPI import, so it is callable
from a worker or CLI; `repositories/` is the only place SQL is written, so swapping
Postgres for anything else touches one directory.

---

## 1. Schemas

Two distinct families. **Pydantic schemas** (`src/schemas/`) define the wire contract.
**ORM models** (`src/models/`) define storage. They are deliberately separate — the API
shape is nested and read-optimised, the tables are flat and normalised.

### 1.1 Pydantic — `src/schemas/`

| File | Holds | Notes |
| --- | --- | --- |
| `enums.py` | Every enum, shared by ORM and wire | `SCREAMING_SNAKE_CASE` on the wire; persisted as constrained TEXT, so adding a value is a code change, not a migration |
| `validators.py` | `clean_text`, `slugify`, `validate_https_url`, `validate_video_url` | https-only, blocks localhost/private ranges (SSRF), rejects control characters |
| `common.py` | `Schedule`, `Budget`, `Delivery`, `Compliance`, `Tracking`, `CampaignMetrics`, `StrictModel` | `StrictModel` forbids unknown keys, so a payload typo is an error not a silent no-op |
| `campaign.py` | `CampaignCreate`, `CampaignUpdate`, `CampaignRead`, `CampaignListItem`, `CampaignPage`, `StatusChange` | Write schemas carry only user-controlled fields |
| `experience.py` | `ExperienceInput`, `ExperienceRead`, `ExperiencePublic` | `*Public` is the recipient-safe variant |
| `option.py` | `OptionInput`, `OptionRead`, `OptionPublic` | `OptionPublic` omits the follow-up so a recipient cannot read the outcome they did not choose |
| `recipient.py` | `RecipientInput`, `RecipientRead`, `Audience` | |
| `event.py` | `ViewEventCreate`, `ResponseEventCreate`, `EventRead`, `ResponseResult` | |
| `analytics.py` | `CampaignAnalytics`, `OptionBreakdown`, `TimeseriesPoint` | |
| `preview.py` | `CampaignPreview`, `PreviewCompliance` | Built from an explicit allow-list — the only unauthenticated response |
| `health.py` | `HealthResponse` | |

**Read-only fields.** `effective_status`, `badge`, `metrics` and `publish_blockers` appear
on `GET` and are ignored on write, so a client echoing a GET payload back cannot corrupt
state. `owner_user_id` is never accepted from a payload at all — it comes from the Clerk
session.

**Draft vs. publish.** `CampaignCreate` requires only `name`. The full contract is enforced
at publish time by `publish_validator.py`, mirroring how a half-built campaign can be saved
but not run.

### 1.2 ORM — `src/models/`

Five tables, every child cascading from `campaigns`.

| File | Table | Key points |
| --- | --- | --- |
| `campaign.py` | `campaigns` | Aggregate root. `owner_user_id` = Clerk user id |
| `experience.py` | `campaign_experiences`, `campaign_options` | Options are **rows**, not `option_1_*` columns |
| `recipient.py` | `campaign_recipients` | Single-customer case is a one-row list |
| `event.py` | `campaign_events` | `campaign_id` denormalised so analytics never joins through experiences |
| `types.py` | — | `UTCDateTime`: SQLite returns naive datetimes, Postgres aware ones; this normalises both |
| `mixins.py` | — | `UUIDPrimaryKey` (CHAR(36), identical on both engines), `TimestampMixin` |

**Indexes that carry rules**

| Index | Enforces |
| --- | --- |
| `uniq_campaign_owner_name` on `(owner_user_id, lower(name))` | Case-insensitive name uniqueness **per Clerk user** |
| `uniq_view_per_session` — partial, `type='VIEW'` | One view per session |
| `uniq_response_per_session` — partial, `type='RESPONSE'` | One response per session |
| `uniq_option_position` on `(experience_id, position)` | Exactly one option per slot |
| `idx_events_campaign_type` | Analytics aggregation |

Duplicate protection lives in the **database**, not just the service, so two concurrent
requests cannot both insert. Partial indexes behave identically on SQLite and Postgres.

### PostgreSQL

Postgres is the deployment target, over `asyncpg`. Schema choices that assume it:

- `JSONB` for `campaign_recipients.attributes` (plain `JSON` on SQLite via a dialect variant)
- Partial unique indexes for event deduplication
- A functional unique index on `(owner_user_id, lower(name))`
- Money as `BIGINT` minor units — never a float
- Enums as constrained `TEXT`, so adding a value is a code change, not a migration

> **Alembic autogenerate cannot see functional indexes.** `uniq_campaign_owner_name` was
> silently absent from the generated migration, which would have left campaign-name
> uniqueness unenforced on any database built from migrations — while passing every test,
> because the test schema came from `create_all`. It is now written explicitly with
> `op.execute`, and `tests/test_migrations.py` fails if any declared index goes missing.

The suite runs on both engines: SQLite by default for speed, and PostgreSQL via
`TEST_DATABASE_URL`. CI runs both, and additionally applies and rolls back the
migrations against a real Postgres service.

---

## 2. Services

No FastAPI imports anywhere in this directory. Services raise `ApiError`; the registered
handler turns it into the response envelope.

| File | Owns |
| --- | --- |
| `campaign_service.py` | Create, partial update, lifecycle transitions, name conflicts, audience rules |
| `event_service.py` | View/response recording, deduplication, follow-up resolution, IP hashing |
| `analytics_service.py` | Aggregation — views, interactions, rate, per-option split, primary metric |
| `preview_service.py` | Recipient-facing render with personalisation resolved |
| `personalisation.py` | `{{customer_name}}` substitution |
| `status_service.py` | `effective_status`, dashboard `badge`, legal transitions |
| `publish_validator.py` | The publish contract → a list of `Blocker`s |
| `mappers.py` | ORM → wire schema, in one place |
| `validators_utm.py` | UTM append; params already on the destination win |
| `health_service.py` | Liveness/readiness |

### Decisions worth knowing

**Deduplication returns 200, not 409.** A repeat call returns the *original* event with
`deduplicated: true`. A double-click is not a client error, and the preview page must not
show a failure state for one. A repeat response returns the follow-up for the option
**originally chosen**, so a double-click cannot switch the outcome.

**Status is derived, not scheduled.** `effective_status` is computed per request from
status + schedule + completeness. A campaign becomes `ACTIVE` when its start time passes
and `COMPLETED` when it ends, with no cron process.

**Publish blockers do double duty.** The same function gates publishing (422 with
field-level details) and populates `publish_blockers` on every read, so the builder can
disable the button and say exactly what is missing without attempting the call.

**Options reconcile by position.** Clearing and re-adding makes SQLAlchemy emit the INSERT
before the DELETE in one flush, tripping `uniq_option_position`. Updating in place also
preserves each option's analytics `key`, so rewording "Tell me more" to "Yes, I'm
interested" does not split the metric into two series.

**Interaction rate never divides by zero** — a campaign with no views reports `0.0`.

---

## 3. Routing

`src/app/router.py` mounts two routers. Operational routes sit at the root so platform
probes reach them without knowing the version prefix; everything else is under
`API_PREFIX` (default `/api/v1`).

### Authenticated — Clerk session required

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/campaigns` | Dashboard listing. `?status=` `?search=` `?include_archived=` `?limit=` `?offset=` |
| `POST` | `/api/v1/campaigns` | Create (201 + `Location`) |
| `GET` | `/api/v1/campaigns/{id}` | Full read |
| `PATCH` | `/api/v1/campaigns/{id}` | Partial update |
| `POST` | `/api/v1/campaigns/{id}/status` | Publish / pause / resume / unpublish / archive |
| `DELETE` | `/api/v1/campaigns/{id}` | Delete campaign and its events (204) |
| `GET` | `/api/v1/campaigns/{id}/preview` | Owner preview — works at **any** status, so drafts can be checked |
| `GET` | `/api/v1/campaigns/{id}/analytics` | Aggregate metrics |

### Public — recipient-facing, no session

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/public/campaigns/{id}` | Open a live campaign. 403 unless effective status is `ACTIVE` |
| `POST` | `/api/v1/public/campaigns/{id}/views` | Record a view. Idempotent per `session_id` |
| `POST` | `/api/v1/public/campaigns/{id}/responses` | Record a response, return the follow-up |

### Operational

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/healthz` | 200 healthy, 503 degraded |
| `GET` | `/docs` · `/redoc` · `/openapi.json` | Generated API documentation |

### Status codes

| Code | When |
| --- | --- |
| `200` | Read, update, or a **deduplicated** event |
| `201` | Campaign created, or a first-time event |
| `204` | Deleted |
| `401` | `NOT_AUTHENTICATED` — no valid Clerk session |
| `403` | `CAMPAIGN_NOT_LIVE` — recipient opened a non-active campaign |
| `404` | `CAMPAIGN_NOT_FOUND` — unknown id, **or owned by someone else** |
| `409` | `CAMPAIGN_NAME_TAKEN`, `CAMPAIGN_INVALID_TRANSITION`, `CAMPAIGN_LOCKED` |
| `422` | `VALIDATION_ERROR`, `EVENT_INVALID_OPTION` |

> A campaign owned by another Clerk user returns **404, never 403**, so ids cannot be
> probed for existence.

---

## 4. Authentication — Clerk

Clerk owns sign-up, sign-in, sessions and the user record. This service **never issues,
stores or validates credentials**. There is no local users table and no auth endpoints.

1. The frontend obtains a Clerk session JWT.
2. It sends `Authorization: Bearer <jwt>`.
3. `ClerkVerifier` (`src/core/security.py`) verifies the signature against Clerk's JWKS
   and reads `sub`.
4. That id becomes `campaigns.owner_user_id`.

JWKS keys are cached in memory; the fetch is synchronous so it runs in a worker thread
rather than blocking the event loop.

**Development fallback.** Before Clerk keys exist, `X-Dev-User-Id` asserts an identity
directly. It is gated by `ALLOW_DEV_AUTH_HEADER`, and **startup fails** if that is true
while `ENVIRONMENT=production` — along with `DEBUG=true`, missing Clerk config, or a
default `IP_HASH_SALT`.

Clerk also supersedes the multi-tenancy question the data model left open: `owner_user_id`
scopes every query, so no `workspace_id` is needed for single-user ownership.

---

## 5. Error envelope

Every failure — validation, HTTP, or unexpected — returns one shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The campaign cannot be published.",
    "details": [
      { "field": "experience.video_url", "code": "REQUIRED", "message": "A video URL is required before publishing." }
    ]
  }
}
```

`details` is **always an array**, so the frontend maps it onto field-level messages without
branching on shape. Request-validation errors are normalised into the same
`{field, code, message}` form the publish contract produces — Pydantic's raw errors embed
the original exception object, which is not JSON-serialisable.

---

[← Index](README.md) · [Campaign Data Model](campaign-data-model.md) · [Backend Requirements](04-backend-requirements.md)
