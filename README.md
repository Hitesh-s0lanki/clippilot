# ClipPilot

**Mini Interactive Video Campaign Builder.** A marketer creates a personalised video
campaign; a customer opens it, watches, and clicks one of two response options; the click
lands in the campaign's analytics within the same session.

[![Backend CI](https://github.com/Hitesh-s0lanki/clippilot/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Hitesh-s0lanki/clippilot/actions/workflows/backend-ci.yml)

```
Dashboard ──▶ Builder ──▶ Customer Preview ──▶ Response click ──▶ Analytics
    ▲                                                                 │
    └─────────────────────── event recorded ──────────────────────────┘
```

| | |
| --- | --- |
| **Frontend** | Next.js 16 App Router · React 19 · TypeScript · Tailwind v4 · shadcn/ui |
| **Backend** | FastAPI · SQLAlchemy 2 (async) · Alembic · Python 3.12 |
| **Database** | PostgreSQL (deployment target) · SQLite (zero-setup local run) |
| **Auth** | Clerk — hosted sign-in; the API verifies the session JWT against JWKS |
| **Live demo** | _not deployed — see [Known limitations](#known-limitations)_ |
| **Screen recording** | _TODO: add link_ |
| **Time spent** | _TODO: state total hours_ |

---

## 1. Install and run

Requires **Node.js 20.9+**, **Python 3.12+**, [**uv**](https://docs.astral.sh/uv/), and
PostgreSQL 14+ (optional — SQLite works out of the box).

### Backend

```bash
cd backend
uv sync                      # creates .venv, installs runtime + dev deps
cp .env.example .env         # then set DATABASE_URL and the Clerk values
uv run alembic upgrade head  # apply migrations
uv run uvicorn src.main:app --reload
```

API on **http://localhost:8000** · Swagger UI at `/docs` · health probe at `/healthz`.

**Database.** PostgreSQL is the deployment target, over `asyncpg`:

```bash
createdb trustvid
DATABASE_URL=postgresql+asyncpg://trustvid:trustvid@localhost:5432/trustvid
```

For a zero-setup run, point it at SQLite instead — this is also what the test suite uses:

```bash
DATABASE_URL=sqlite+aiosqlite:///./trustvid.db
```

> On managed Postgres (Neon, Supabase, RDS) use the **pooled** connection string and
> delete any `?sslmode=` parameter — `asyncpg` rejects it and negotiates TLS itself.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # then add the Clerk keys
npm run dev
```

App on **http://localhost:3002**. The backend must be running — the home page probes
`GET /healthz` on every request, so a stopped API shows up immediately rather than as an
empty screen three clicks later.

> **Point both sides at the same Clerk application**, or every campaign request returns
> `401`. Create one at [dashboard.clerk.com](https://dashboard.clerk.com); the frontend
> needs the publishable and secret keys, the backend needs the matching issuer and JWKS
> URL.

Full per-service detail: [`backend/README.md`](backend/README.md) ·
[`frontend/README.md`](frontend/README.md).

---

## 2. Environment variables

Example values only — real values never enter the repository. Complete, commented
templates live in [`backend/.env.example`](backend/.env.example) and
[`frontend/.env.example`](frontend/.env.example).

### `backend/.env`

| Variable | Example | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | `production` forbids the dev auth header |
| `API_PREFIX` | `/api/v1` | Business routes mount here; `/healthz` stays at root |
| `CORS_ORIGINS` | `http://localhost:3002` | Comma-separated browser origins |
| `DATABASE_URL` | `postgresql+asyncpg://trustvid:trustvid@localhost:5432/trustvid` | `asyncpg` or `aiosqlite` driver required |
| `CLERK_ISSUER` | `https://your-app.clerk.accounts.dev` | Must match the frontend's Clerk app |
| `CLERK_JWKS_URL` | `https://your-app.clerk.accounts.dev/.well-known/jwks.json` | Public keys for JWT verification |
| `ALLOW_DEV_AUTH_HEADER` | `true` | Dev only — accept `X-Dev-User-Id` instead of a real token. Startup **fails** if true in production |
| `IP_HASH_SALT` | `dev-only-change-me` | Salt for event IP hashing; raw IPs are never stored |
| `S3_BUCKET` | *(empty)* | Empty disables uploads — the builder then accepts a pasted `https` video URL and no AWS account is needed |

### `frontend/.env.local`

| Variable | Example | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Inlined at build time — must be set when `next build` runs |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_test_replace-me` | Fails fast by name if missing |
| `CLERK_SECRET_KEY` | `sk_test_replace-me` | Server-side only |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/login` | Clerk reads redirect URLs from the environment |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/register` | |

---

## 3. Technology choices

| Choice | Why |
| --- | --- |
| **Next.js App Router, Server Components by default** | The dashboard, analytics and preview screens are read-heavy. Fetching on the server keeps the API base URL and session token off the client and removes a loading spinner from the common path. `"use client"` sits on the smallest leaf that needs it. |
| **FastAPI over Django/Flask** | Pydantic gives request/response validation and a generated OpenAPI schema from the same type definitions, which is most of the "input validation and sanitisation" requirement for free. |
| **SQLAlchemy 2 async + Alembic** | Real migrations rather than `create_all`. Alembic owns the schema; tables auto-create at startup **only** on SQLite. |
| **PostgreSQL as the target, SQLite for convenience** | Every schema decision targets Postgres — `JSONB` recipient attributes, partial unique indexes for event dedup, a functional unique index on `lower(name)`. SQLite keeps a reviewer's setup to one command. CI runs the suite on both. |
| **Clerk for auth** | Campaigns are owner-scoped, so identity was needed, but hand-rolling sessions is not what this assignment measures. The API only verifies a JWT against JWKS — no user table, no password handling. |
| **Layered backend** (`controllers → services → repositories`) | Business logic stays testable without an HTTP client, and swapping persistence touches one directory. Controllers hold no business rules; services import no framework. |
| **Options and recipients as rows, not columns** | `option_1_label` / `option_2_label` cannot grow to three options and cannot be aggregated without a `UNION`. The single-customer case is simply a one-row recipient list. |
| **shadcn/ui + semantic Tailwind tokens** | Components are owned in-repo rather than versioned as a dependency. Styling goes through `bg-card` / `text-foreground` / `border-border`, so light and dark themes come from one token set. |

---

## 4. API summary

Business routes mount under `API_PREFIX` (default `/api/v1`). Operational routes sit at
the root so platform probes reach them without knowing the version.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/healthz` | — | Health probe; `503` when a dependency check fails |
| `GET` | `/api/v1/campaigns` | Clerk | List the caller's campaigns (filter, search, paginate) |
| `POST` | `/api/v1/campaigns` | Clerk | Create a campaign |
| `GET` | `/api/v1/campaigns/{id}` | Clerk | Fetch one campaign |
| `PATCH` | `/api/v1/campaigns/{id}` | Clerk | Update fields |
| `POST` | `/api/v1/campaigns/{id}/status` | Clerk | Lifecycle transition — its own action route, not a `PATCH` field |
| `DELETE` | `/api/v1/campaigns/{id}` | Clerk | Archive (soft delete) |
| `GET` | `/api/v1/campaigns/{id}/preview` | Clerk | Owner-side resolved preview |
| `GET` | `/api/v1/campaigns/{id}/analytics` | Clerk | Views, interactions, rate, per-option breakdown |
| `GET` | `/api/v1/uploads/config` | Clerk | Upload limits and whether S3 is configured |
| `POST` | `/api/v1/uploads/video` | Clerk | Presigned upload target |
| `POST` | `/api/v1/uploads/video/complete` | Clerk | Finalise an upload, return the public URL |
| `GET` | `/api/v1/public/campaigns/{id}` | — | Recipient-facing campaign payload |
| `POST` | `/api/v1/public/campaigns/{id}/views` | — | Record a view |
| `POST` | `/api/v1/public/campaigns/{id}/responses` | — | Record a response click |

**Error envelope.** Every failure — validation, HTTP, or unexpected — returns one shape:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [] } }
```

`details` is **always an array**, even for a single error, so the frontend maps it onto
fields without branching on shape.

**Event integrity.** `occurred_at` comes from the server clock, never the client. Raw IPs
are never stored — only a salted hash. A duplicate event returns `200` with
`"deduplicated": true` rather than `409`, because a retrying browser is not a client
error; partial unique indexes enforce this at the database level.

---

## 5. Data model

The campaign is a **top-level entity** — objective, lifecycle, schedule, budget, audience,
compliance and tracking — with the video experience nested beneath it, modelled on the Meta
Ads campaign object.

```
campaigns ──1:N──▶ campaign_experiences ──1:N──▶ campaign_options
    ├──1:N──▶ campaign_recipients
    └──1:N──▶ campaign_events
```

| Table | Holds |
| --- | --- |
| `campaigns` | Name, objective, status, schedule, budget, compliance, UTM tracking, owner |
| `campaign_experiences` | The creative: video URL, headline, personalised message |
| `campaign_options` | One row per response option — stable `key`, label, intent, follow-up |
| `campaign_recipients` | One row per recipient; `JSONB` attributes for personalisation |
| `campaign_events` | `VIEW` and `RESPONSE` events, deduplicated per session |

Status is stored (`DRAFT`, `SCHEDULED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED`) while
**`effective_status` is computed on read** from the stored status and the schedule window
— so a campaign becomes active on time without a scheduler process running anywhere.

Full specification — every column, enum, index, validation rule and error code:
[`docs/campaign-data-model.md`](docs/campaign-data-model.md).
Service and routing layout: [`docs/backend-architecture.md`](docs/backend-architecture.md).

---

## 6. Features completed

**Core flow — works end to end.** Dashboard → builder → save → customer preview →
response click → analytics reflects the event.

- **Dashboard** — campaign cards with status badge, objective, schedule window, recipient
  count and view/interaction metrics; status and objective filters, name search,
  pagination, empty and loading states.
- **Builder** — campaign, experience, options, audience, schedule, compliance, delivery and
  tracking sections; `{{customer_name}}` personalisation; per-option intent and follow-up
  (message *or* URL); direct video upload to S3 with progress, or a pasted `https` URL.
  Draft saves with only a name; **publish** enforces the full contract and reports *every*
  unmet field at once via a publish checklist, not one failure per attempt.
- **Customer preview** — public route at `/preview/{campaignId}`, no sign-in. Video plays,
  `{{customer_name}}` resolves (falling back to `there`), values are HTML-escaped, the
  compliance disclaimer renders when a special category is set, and a non-live campaign is
  blocked with `403 CAMPAIGN_NOT_LIVE`. Duplicate events are suppressed within a session.
- **Analytics** — views, interactions, interaction rate, unique viewers, per-option clicks
  with a percentage split bar, objective-driven primary metric, first/last activity. The
  rate is `0` when views is `0` — no `NaN`, no divide-by-zero — and zero-click options
  still return a row so the breakdown never has a missing bar.
- **Lifecycle** — a state machine rejects illegal transitions with `409`, the objective
  freezes after publish, unpublish is blocked once events exist, and option `key`s survive
  label edits so historical analytics stay attributable.
- **Quality gates** — 94 backend tests pass; `ruff` lint and format; frontend `eslint`,
  Prettier and `tsc --noEmit` all clean. CI runs the suite on Python 3.12 and 3.13, against
  both SQLite and a real PostgreSQL 17 service, plus a runtime-deps-only boot smoke test.

## Not completed

- **Sending.** Campaigns are built and previewed; there is no delivery channel — no email
  or SMS dispatch, no send queue, no per-recipient tracked link generation.
- **CSV recipient import.** Recipients are added row by row in the builder; there is no
  bulk upload.
- **Analytics timeseries chart.** The API returns daily `timeseries` points; the UI shows
  totals and the split bar but does not yet plot them.
- **A/B experiences.** The schema nests experiences under a campaign to allow variants,
  but only one experience per campaign is created or served.
- **Deployment.** Nothing is hosted; there is no live demo link.

---

## 7. Known limitations

- **No multi-tenancy.** Campaigns are scoped to a Clerk user id. There are no
  organisations, teams, roles or sharing.
- **Analytics are computed per request.** Aggregates run as queries against
  `campaign_events` on every analytics load. Correct and fast at assignment scale; a
  campaign with millions of events needs rollup tables or a warehouse.
- **View events are best-effort.** A recipient who blocks scripts, or leaves before the
  player initialises, records no view — so interaction rate is an upper bound.
- **Session dedup is client-scoped.** A cleared browser session or a second device counts
  as a new viewer. Unique-viewer counts are approximate by design, since the alternative
  is identifying people more aggressively than this product should.
- **No video processing.** URLs are validated (`https`, public hostname, to block SSRF) and
  uploads are stored, but nothing transcodes, generates posters, or checks duration and
  codec. A recipient's browser either plays the file or does not.
- **Rate limiting is absent.** The public event endpoints dedupe but do not throttle; a
  script could inflate counts. Real deployment needs a limiter at the edge.

### What I would build next

1. **Send execution** — the missing half of the loop: a delivery channel, per-recipient
   tracked links, and delivery/open events alongside view and response.
2. **Scheduler-backed lifecycle** — `effective_status` computed on read is correct and
   process-free, but real campaigns need transition side effects (notify on start, finalise
   on completion), which means a job runner.
3. **Analytics depth** — plot the timeseries the API already returns, add funnel and
   time-to-first-interaction, and precompute rollups.
4. **A/B experiences** — the schema already nests experiences under a campaign; the work is
   allocation, exposure logging and a significance readout.
5. **Rate limiting and abuse controls** on the public endpoints.

---

## 8. AI tools used

Built with **Claude Code** (Claude Opus) as the primary development tool, used for
scaffolding, implementation and review across both services. The repository carries its
working configuration so the process is inspectable rather than implied:

- [`CLAUDE.md`](CLAUDE.md) — repo-level architectural constraints given to the agent.
- [`.claude/skills/`](.claude/skills/) — the frontend structure, component-size and UI/UX
  rules enforced during generation.
- [`design-system/clippilot/MASTER.md`](design-system/clippilot/MASTER.md) — the design
  system the UI was built against.

Every generated change was reviewed before commit; the architecture, data model and the
decisions in §3 are mine, and the documents in [`docs/`](docs/) were written first and used
to constrain what was generated.

---

## Repository layout

| Path | Contents |
| --- | --- |
| [`frontend/`](frontend/) | Next.js app — route groups, per-route `_components/`, `src/lib/api` |
| [`backend/`](backend/) | FastAPI service — `controllers`, `services`, `repositories`, `models`, `schemas` |
| [`docs/`](docs/) | Architecture and data-model design notes |
| [`design-system/`](design-system/) | Visual language the UI is built against |
| [`.github/workflows/`](.github/workflows/) | Backend CI pipeline |

> **Note on the source brief.** This project was built against an assignment document
> marked *CONFIDENTIAL — CANDIDATE EVALUATION*. That file and the transcription of its
> sections are deliberately excluded from this public repository; the design documents in
> [`docs/`](docs/) are original work. See [`docs/README.md`](docs/README.md).
