# ClipPilot Backend

FastAPI service for the ClipPilot interactive video campaign builder.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 14+ (the deployment target)

## Setup

```bash
cd backend
uv sync                 # creates .venv and installs runtime + dev dependencies
cp .env.example .env    # then set DATABASE_URL to the hosted instance
uv run alembic upgrade head
```

### Database

The database is a **hosted Neon PostgreSQL instance**, reached over the
`asyncpg` driver. There is nothing to install and nothing to create - every
environment points at that one instance.

Neon hands out a URL that `asyncpg` cannot use as given, and both problems are
quiet ones:

```
given:  postgresql://…@ep-xxx.<region>.aws.neon.tech/neondb?sslmode=require&channel_binding=require
use:    postgresql+asyncpg://…@ep-xxx.<region>.aws.neon.tech/neondb
```

`postgresql://` resolves to psycopg2, which is not installed, so the driver has
to be named. `sslmode` and `channel_binding` make `asyncpg` raise `invalid
connection option` rather than ignoring them - it negotiates TLS itself.
[`scripts/sync-github-secrets.sh --database-url`](scripts/sync-github-secrets.sh)
does both conversions for you. Prefer the `-pooler` host once concurrent
connections matter.

SQLite still works for a zero-setup run (`sqlite+aiosqlite:///./trustvid.db`) and is
what the test suite uses by default, but every schema decision targets Postgres:
`JSONB` for recipient attributes, partial unique indexes for event deduplication,
and a functional unique index on `lower(name)`.

> The test suite never reads `DATABASE_URL`. `tests/conftest.py` uses
> `TEST_DATABASE_URL`, falling back to a temporary SQLite file, so its
> `drop_all` cannot reach the hosted database however `.env` is set.

### Migrations

Alembic owns the schema. Tables are auto-created at startup only on SQLite, and only
when the file is **new** — a database Alembic has already stamped is left to Alembic.

```bash
uv run alembic upgrade head                          # apply
uv run alembic revision --autogenerate -m "message"  # create
uv run alembic downgrade -1                          # roll back one
```

> Autogenerate cannot see **functional indexes**. `uniq_campaign_owner_name`
> (`lower(name)`) is written by hand with `op.execute`, and
> `tests/test_migrations.py` fails if any declared index goes missing from the
> migrations.

**If startup refuses with "this SQLite database is at migration X but the code expects
Y"**, run `uv run alembic upgrade head`, or delete the file to start from an empty one.

That check exists because `create_all` is not a migration. On a database stamped at an
older revision it adds the tables that are missing and silently leaves the existing ones
alone, which produces a hybrid: new tables, empty, beside old tables holding the data, and
an existing table missing the column the ORM now expects. The first query then fails with
`no such column: campaigns.audience_id` — a long way from the cause. Refusing to start is
the cheaper failure.

Repairing a database already in that state means dropping the empty tables `create_all`
invented, then upgrading, so the migrations can do their renames and carry the data:

```bash
cp trustvid.db trustvid.db.bak-$(date +%H%M%S)
sqlite3 trustvid.db 'DROP TABLE ad_options; DROP TABLE campaign_ads;'  # whichever are empty
uv run alembic upgrade head
```

### Demo data

```bash
uv run python -m scripts.seed_audiences  --owner <clerk-user-id>   # 100 people, three lists
uv run python -m scripts.seed_campaigns  --owner <clerk-user-id>   # 4 campaigns, 6 ads
```

Both are idempotent — anything the account already has by name is left alone, so running
them twice does not duplicate. Campaigns need the audiences first.

The seeded campaigns sit at different points of the lifecycle on purpose: two published
and two draft, one published campaign with a **paused** ad, and one draft ad with **no
video** so the `INCOMPLETE` state and the publish blockers have something to describe. The
videos are real CC0 files, so the preview actually plays.

## Run

```bash
uv run uvicorn src.main:app --reload
```

| URL | Purpose |
| --- | --- |
| http://localhost:8000/healthz | Health probe |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | OpenAPI schema |

## Test

```bash
uv run pytest              # full suite (SQLite, fast)
uv run pytest -v           # verbose
uv run ruff check .        # lint
uv run ruff format .       # format
```

Run the same suite against PostgreSQL — CI does both:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://trustvid@localhost:5432/trustvid_test uv run pytest
```

The suite drops and recreates the schema per test when pointed at Postgres, so
give it a **dedicated database**, never a development one.

## Data model

The campaign is a **top-level entity** — objective, lifecycle, schedule, budget,
audience, compliance and tracking — with one or more **ads** nested beneath it.
Tables, enums, indexes, validation rules and error codes are specified in
[`docs/campaign-data-model.md`](../docs/campaign-data-model.md).

```
campaigns ──1:N──▶ campaign_ads ──1:N──▶ ad_options   (at most 5 ads)
    ├──N:1──▶ audiences ──1:N──▶ audience_members
    └──1:N──▶ campaign_events
```

## Continuous integration

[`.github/workflows/backend-ci.yml`](../.github/workflows/backend-ci.yml) runs on
pushes and pull requests that touch `backend/**`, ignoring Markdown-only edits.

| Job | What it does |
| --- | --- |
| `quality` | `ruff check` (annotates the PR diff) and `ruff format --check`; asserts `uv.lock` matches `pyproject.toml` |
| `test` | `pytest` with coverage on Python 3.12 and 3.13 (SQLite); uploads HTML coverage and JUnit reports |
| `test-postgres` | Applies migrations to a real PostgreSQL 17 service, verifies they roll back, runs the suite against it |
| `smoke` | Installs **runtime dependencies only**, boots uvicorn and probes `/healthz` over HTTP |
| `backend-ci` | Single gate job to require in branch protection |

Reproduce the whole pipeline locally:

```bash
uv sync --locked --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov --cov-report=term-missing
bash ./scripts/smoke.sh
```

The smoke test exists because the in-process test suite cannot catch import
errors at module scope, lifespan failures, or a bad host/port binding - the
things that break a deploy while every unit test still passes.

## Architecture

Each layer depends only on the one beneath it, so business logic stays testable
without an HTTP client and swapping the persistence layer touches one directory.

```
request
   ↓
src/app/router.py            route registry - maps URLs to controllers
   ↓
src/controllers/             HTTP in / HTTP out, no business rules
   ↓
src/services/                business logic, no framework imports
   ↓
(repositories)               database access - added with the persistence layer
```

```
backend/
├── src/
│   ├── main.py                        # create_app() factory + lifespan
│   ├── app/
│   │   ├── router.py                  # root_router + versioned api_router
│   │   ├── dependencies.py            # DI providers (settings, services)
│   │   └── errors.py                  # ApiError + consistent error envelope
│   ├── controllers/health_controller.py
│   ├── services/health_service.py
│   ├── schemas/health.py              # Pydantic request/response models
│   └── core/config.py                 # environment-backed Settings
└── tests/
    ├── conftest.py                    # settings / app / client fixtures
    ├── test_health_service.py         # unit tests, no HTTP
    └── test_healthz.py                # integration tests through the ASGI stack
```

### Route conventions

- **Operational routes** (`/healthz`) sit at the root so platform probes reach
  them without knowing the version prefix.
- **Business routes** mount under `API_PREFIX` (default `/api/v1`) via
  `api_router`.

### Error envelope

Every failure — validation, HTTP, or unexpected — returns the same shape:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [] } }
```

Raise `ApiError(404, "CAMPAIGN_NOT_FOUND", "No campaign with that id.")` from any
layer to produce it. `details` is **always an array**, even for a single error, so
the frontend maps it onto fields without branching on shape. The full code table is
in [`docs/campaign-data-model.md`](../docs/campaign-data-model.md#error-codes).

## `GET /healthz`

Returns `200` when healthy, `503` when any dependency check fails.

```json
{
  "status": "ok",
  "service": "ClipPilot API",
  "version": "0.1.0",
  "environment": "development",
  "uptime_seconds": 12.48,
  "timestamp": "2026-08-21T11:47:22.435514Z"
}
```

Dependency probes are registered in `HealthService._check_dependencies()`. It
returns an empty dict today; add the database ping there and `status` flips to
`degraded` automatically.

## Environment variables

See [`.env.example`](.env.example). All have defaults suitable for local
development.

| Variable | Default | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | `development` \| `test` \| `production` |
| `DEBUG` | `false` | |
| `PROJECT_NAME` | `ClipPilot API` | Shown in OpenAPI + `/healthz` |
| `VERSION` | `0.1.0` | |
| `API_PREFIX` | `/api/v1` | Prefix for business routes |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated |
| `S3_BUCKET` | *(empty)* | Empty disables uploads entirely |
| `S3_REGION` | `ap-south-1` | |
| `S3_KEY_PREFIX` | `campaign-videos` | Folder inside the bucket |
| `S3_PUBLIC_BASE_URL` | *(empty)* | CloudFront origin; falls back to the bucket URL. Must be https |
| `S3_OBJECT_ACL` | *(empty)* | Leave empty unless the bucket still has ACLs enabled |
| `S3_UPLOAD_EXPIRES_SECONDS` | `900` | Presigned ticket lifetime |
| `MAX_VIDEO_UPLOAD_BYTES` | `209715200` | 200 MB, enforced by the signed policy |
| `ALLOWED_VIDEO_CONTENT_TYPES` | `video/mp4,video/webm,video/quicktime` | |
| `ANTHROPIC_API_KEY` | *(empty)* | Empty disables every `/agents` endpoint |
| `AGENT_MODEL` | `claude-opus-5` | |
| `AGENT_EFFORT` | `high` | `low` \| `medium` \| `high` \| `xhigh` \| `max` |
| `AGENT_MAX_TOKENS` | `16000` | Covers thinking *and* the answer |
| `AGENT_MAX_STEPS` | `12` | Model turns per run |
| `AGENT_TIMEOUT_SECONDS` | `240` | Wall clock for a whole run |
| `FIRECRAWL_API_KEY` | *(empty)* | Empty degrades research; it does not disable agents |
| `FIRECRAWL_MCP_URL` | `https://mcp.firecrawl.dev/v2/mcp` | Key travels as a bearer token, never in the URL |
| `FIRECRAWL_MCP_TIMEOUT_SECONDS` | `90` | |

## Video uploads (AWS S3)

An ad needs a playable `video_url`. A pasted CDN link is still accepted;
these endpoints add the other half - uploading the file itself.

**The bytes never pass through this API.** The backend signs a short-lived S3
policy, the browser POSTs the file straight to the bucket, and a second call
confirms the object landed before the URL is saved on a campaign:

```
POST /api/v1/uploads/video           -> { key, upload_url, fields, video_url }
     browser POSTs the file to `upload_url` with `fields` first, file last
POST /api/v1/uploads/video/complete  -> HEAD confirms it exists -> { video_url }
GET  /api/v1/uploads/config          -> { enabled, max_bytes, accepted_content_types }
```

Streaming a 200 MB upload through a FastAPI worker would hold a connection and a
spooled temp file for its whole duration, so a handful of concurrent uploads is
enough to stall the API. Presigned **POST** is used rather than PUT because only
POST carries a `content-length-range` condition - the size limit is enforced by
S3 itself, not merely checked here, so a tampered client cannot exceed it.

Leaving `S3_BUCKET` empty disables the upload endpoints (`enabled: false`); the
builder then only offers the pasted-URL field and the API runs with no AWS
account at all.

### Bucket setup

Objects are written under `<S3_KEY_PREFIX>/<sha256(owner)[:16]>/<uuid>-<name>.<ext>`.
The owner id is hashed because the key ends up in a public URL.

**1. CORS** - required, and the usual cause of an upload that fails with no
status. The browser POSTs cross-origin, so the bucket has to allow it:

```json
[
  {
    "AllowedMethods": ["POST"],
    "AllowedOrigins": ["https://your-frontend.example.com", "http://localhost:3002"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

**2. Public read** - the recipient's preview page plays the video with no
credential. Serve it through CloudFront (set `S3_PUBLIC_BASE_URL` to the
distribution domain) or, for a bucket read directly, turn off "Block all public
access" and attach:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket/campaign-videos/*"
    }
  ]
}
```

Leave `S3_OBJECT_ACL` empty. Buckets created since April 2023 have Object
Ownership set to *bucket owner enforced*, where sending any ACL fails outright
with `AccessControlListNotSupported`; public read comes from the policy above.

**3. Credentials** - leave `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` blank in
deployment and attach an instance role instead. boto3's own chain picks it up.
The role needs only `s3:PutObject` and `s3:GetObject` on
`arn:aws:s3:::your-bucket/<prefix>/*`.

**4. Lifecycle** *(optional)* - a rule expiring incomplete multipart uploads
after a day keeps abandoned uploads from accruing storage cost.

Note `S3_PUBLIC_BASE_URL` must be **https**: `validate_video_url` rejects
anything else, so a plain-http CDN produces objects that cannot be saved. That
also means a local MinIO on `http://localhost:9000` will upload but not save -
use a real bucket, or a pasted URL, for the end-to-end flow.

## AI agents (LangChain + Firecrawl MCP)

The builder form asks for a name, an objective, an audience type, a budget, a compliance
category, tracking parameters, a headline, a personalised message and two response options
with their follow-ups. Most users will not fill that in from nothing.

`POST /api/v1/agents/campaign-strategist/draft` takes a sentence of intent and, when there
is one, the business's website. It reads that site, finds and reads the competitors, and
returns a draft shaped exactly like `CampaignCreate` — plus the analysis behind it and a
per-field confidence, so the user can see what was read and what was guessed.

```bash
curl -X POST http://localhost:8000/api/v1/agents/campaign-strategist/draft \
  -H 'X-Dev-User-Id: user_dev' -H 'Content-Type: application/json' \
  -d '{
        "requirements": "Win back investors who paused their SIP this year.",
        "website_url": "https://example.com",
        "market": "India"
      }'
```

| Endpoint | Purpose |
| --- | --- |
| `GET /agents` | Catalogue: every agent, its JSON Schemas, and whether the feature is on |
| `POST /agents/campaign-strategist/draft` | Typed — what the builder calls |
| `POST /agents/{agent_name}/runs` | Generic — a new agent is callable the moment it registers |

**Two switches, not one.** `ANTHROPIC_API_KEY` empty turns the endpoints off and they
answer `503 AGENTS_NOT_CONFIGURED`. `FIRECRAWL_API_KEY` empty does *not*: the agent still
drafts from the user's brief, sets `researched: false`, and the response comes back with
`meta.degraded: true` and a note saying what was missing. Research improves an answer; it
is not what makes one possible.

Design notes — why structured output is a terminal tool rather than a second constrained
call, why a rejected result is repaired instead of raised, and what it takes to add the
next agent — are in [`docs/agents.md`](../docs/agents.md).

## Dependencies

`pyproject.toml` + `uv.lock` are the source of truth. The exported files are for
platforms that install with pip:

```bash
uv export --format requirements-txt --no-hashes --no-dev --no-emit-project -o requirements.txt
uv export --format requirements-txt --no-hashes --only-dev --no-emit-project -o requirements-dev.txt
```

## Docker

[`Dockerfile`](Dockerfile) builds a two-stage image: the first stage resolves
`uv.lock` into `/app/.venv`, the second carries only that virtualenv and the
source. The result is ~106 MB, runs as uid 1001, and needs no `apt` packages -
the `HEALTHCHECK` probes `/healthz` with `urllib` rather than `curl`.

The build context is `backend/`, not the repository root:

```bash
docker build -t clippilot-backend ./backend

docker run --rm -p 8000:8000 \
  -e DATABASE_URL='postgresql+asyncpg://user:pass@host:5432/trustvid' \
  -e IP_HASH_SALT="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  -e CLERK_JWKS_URL='https://your-app.clerk.accounts.dev/.well-known/jwks.json' \
  -e CLERK_ISSUER='https://your-app.clerk.accounts.dev' \
  clippilot-backend
```

`.env` is in [`.dockerignore`](.dockerignore) on purpose. Configuration reaches
the container through the platform's environment; nothing is baked into the
image.

### Entrypoint

[`scripts/docker-entrypoint.sh`](scripts/docker-entrypoint.sh) applies
`alembic upgrade head` and then execs uvicorn. Anything you pass after the
image name replaces that, so the same image is also the migration runner and
the seed runner:

```bash
docker run --rm -e DATABASE_URL=... clippilot-backend alembic current
docker run --rm -e DATABASE_URL=... clippilot-backend alembic upgrade head
docker run --rm -e DATABASE_URL=... clippilot-backend python -m scripts.seed_audiences
```

| Variable | Default | Effect |
| --- | --- | --- |
| `PORT` | `8000` | Port uvicorn binds. Platforms that inject their own are handled |
| `HOST` | `0.0.0.0` | Bind address |
| `WEB_CONCURRENCY` | `1` | uvicorn worker processes |
| `RUN_MIGRATIONS` | `true` | Set `false` on the web process when the platform runs migrations as a separate release command |
| `FORWARDED_ALLOW_IPS` | `*` | Which upstream proxies may set `X-Forwarded-For`. Events hash the client IP, so without `--proxy-headers` every request would hash the load balancer |

The image ships with `ENVIRONMENT=production`, `DEBUG=false` and
`ALLOW_DEV_AUTH_HEADER=false` already set, so a container that boots at all has
passed `Settings.validate_runtime()`.

The entrypoint checks that configuration *before* it touches the database, so a
missing variable is named rather than buried:

```
entrypoint: ERROR: DATABASE_URL is not set.
entrypoint:   Set it in the platform's environment to the pooled connection
entrypoint:   string, with the postgresql+asyncpg:// driver and no ?sslmode=
```

Left to itself, an unset `DATABASE_URL` falls back to the localhost default in
`Settings` and surfaces as `Connect call failed ('127.0.0.1', 5432)` at the
bottom of a forty-line asyncpg traceback, which names neither the variable nor
the fix.

### What the platform has to set

The image carries no configuration. At minimum a deployed service needs:

| Variable | Why |
| --- | --- |
| `DATABASE_URL` | No database exists inside the container |
| `IP_HASH_SALT` | `validate_runtime()` rejects the `dev-only-change-me` placeholder |
| `CLERK_JWKS_URL`, `CLERK_ISSUER` | Required in production; without them no session verifies |
| `CORS_ORIGINS` | The deployed frontend origin, or the browser blocks every call |

`S3_*` and the agent keys are optional - uploads fall back to a pasted URL and
the `/agents` endpoints switch off, while the rest of the API is unaffected.

### Running against the hosted database

There is no local database to stand up. The schema lives on Neon, and every
environment - a container on your laptop, CI's migrate job, the deployed
service - points at that one instance:

```bash
docker run --rm -p 8000:8000 --env-file .env clippilot-backend
```

`--env-file .env` is safe here and only here: the file is in
[`.dockerignore`](.dockerignore), so it is read at *run* time and never copied
into the image.

The container applies migrations on the way up, so a fresh Neon branch needs no
separate setup step. Set `RUN_MIGRATIONS=false` if you would rather it did not.

## Publishing and deploying

[`.github/workflows/backend-docker.yml`](../.github/workflows/backend-docker.yml)
runs on pushes to `main` and `release` that touch `backend/**`, and on manual
dispatch. Correctness is `backend-ci.yml`'s job; this workflow's job is the
artefact.

| Job | What it does |
| --- | --- |
| `build` | Builds and pushes to `ghcr.io/<owner>/clippilot-backend`, tagged `sha-<commit>`, the branch name, plus `latest` on `main` and `prod` on `release`. Outputs a digest-pinned reference |
| `verify` | Pulls that digest, boots it against a throwaway PostgreSQL with `ENVIRONMENT=production`, and asserts `/healthz` is `ok`, `/openapi.json` serves, migrations ran, and the process is not root |
| `migrate` | Manual dispatch only. Runs `alembic upgrade head` against the `DATABASE_URL` secret, using the image just built |
| `deploy` | Posts the verified digest to `RENDER_DEPLOY_HOOK_URL`. Skipped with a note in the run summary when that secret is absent |

`verify` deliberately runs with `ENVIRONMENT=production` so
`validate_runtime()` executes for real - a missing `IP_HASH_SALT` or Clerk
issuer fails in CI rather than on the platform.

It stands up its own throwaway PostgreSQL rather than using the hosted
instance, and that is not a leftover from a local setup. Two reasons: a run
from a pull request branch could otherwise apply a bad migration to the live
database, and `alembic upgrade head` against an already-migrated Neon proves
nothing - only an empty database proves the migrations build the schema.

### Repository secrets and variables

Credentials are **secrets** (write-only, masked in logs); everything else is a
**variable** (readable in the Actions UI, which is what you want for a bucket
name). Every one of them has a harmless fallback in the workflow, so the
pipeline is green on a repository where none are set yet and gets stricter as
each is filled in.

| Secret | Needed for |
| --- | --- |
| `DATABASE_URL` | The `migrate` job. Must be the pooled `postgresql+asyncpg://` URL - no `?sslmode=`, asyncpg rejects it |
| `IP_HASH_SALT` | `verify`. Generate with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | The agents. Both empty disables `/agents` and nothing else |
| `FIRECRAWL_API_KEY` | Agent web research. Absent means `researched=false`, not a failure |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 uploads. Omit both when the deployment uses an instance role |
| `RENDER_DEPLOY_HOOK_URL` | The `deploy` job. Not in `.env` - copy it from the Render service |

| Variable | Needed for |
| --- | --- |
| `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_AUDIENCE` | Session verification |
| `CORS_ORIGINS` | The deployed frontend origin, comma-separated |
| `S3_BUCKET`, `S3_REGION`, `S3_KEY_PREFIX`, `S3_PUBLIC_BASE_URL` | Video uploads |
| `AGENT_PROVIDER`, `AGENT_MODEL` | Pinning a provider or model |
| `FIRECRAWL_MCP_URL` | The MCP endpoint |

[`scripts/sync-github-secrets.sh`](scripts/sync-github-secrets.sh) pushes them
from `.env` in one go. It never prints a value, skips anything empty, and
refuses to push a placeholder - a `dev-only-change-me` salt or a SQLite
`DATABASE_URL` would leave the workflow looking configured when it is not.

```bash
./scripts/sync-github-secrets.sh --dry-run       # names and lengths only
./scripts/sync-github-secrets.sh                 # push
./scripts/sync-github-secrets.sh --database-url  # prompt for the deployment DB
```

`--database-url` exists because `.env` normally holds the SQLite URL for local
work, so there is nothing there worth pushing. It reads the deployment URL from
a hidden prompt - out of the shell history and out of the process list - and
normalises it, which a managed provider's URL always needs:

| Given by the provider | Why it fails | Fixed to |
| --- | --- | --- |
| `postgresql://` | SQLAlchemy resolves that to psycopg2, which is not installed | `postgresql+asyncpg://` |
| `?sslmode=require`, `&channel_binding=require` | asyncpg raises `invalid connection option`; it negotiates TLS itself | dropped |
| `ep-xxx.<region>.aws.neon.tech` | the direct endpoint exhausts connections under a pool | warns, use `ep-xxx-pooler.…` |

Note what this secret is *not* for. The running container reads `DATABASE_URL`
from the platform's own environment - `.env` is in `.dockerignore` and nothing
is baked into the image. The secret exists so the `migrate` job can reach the
deployment database; setting it does not change what the deployed service
connects to. That has to be set on the platform as well.

### Without Docker

Bind to the platform-provided port:

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

Set `ENVIRONMENT=production`, `DEBUG=false` and `CORS_ORIGINS` to the deployed
frontend origin. Point the platform health check at `/healthz`.
