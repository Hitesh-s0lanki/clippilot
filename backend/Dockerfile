# syntax=docker/dockerfile:1.9
# SecretsUsedInArgOrEnv fires on any ENV whose name contains AUTH/KEY/TOKEN.
# The only one here is ALLOW_DEV_AUTH_HEADER, a boolean feature flag pinned
# off. No credential is baked into this image; they all arrive at runtime.
# check=skip=SecretsUsedInArgOrEnv

# Build context is this directory (backend/), not the repository root:
#
#     docker build -t clippilot-backend ./backend
#
# Two stages so the runtime image carries the virtualenv and the source, but
# none of the build tooling, caches or lockfile machinery that produced it.

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.12.5

# --------------------------------------------------------------------------
# Stage 1 - builder: resolve the locked dependency set into /app/.venv.
# --------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=uv /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Dependencies before the project, so editing a file under src/ reuses this
# layer instead of re-resolving 200 wheels. --frozen installs exactly what
# uv.lock pins and never re-resolves; CI already proves the lock is current
# (`uv lock --check` in backend-ci.yml), so a build must not silently drift.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project

# README.md is here because pyproject declares it as the package readme and
# hatchling refuses to build the wheel without it.
COPY pyproject.toml uv.lock alembic.ini README.md ./
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# A checkout that lost the executable bit (Windows, a zip export) would
# otherwise produce an image whose entrypoint cannot run.
RUN chmod +x scripts/docker-entrypoint.sh

# --------------------------------------------------------------------------
# Stage 2 - runtime.
# --------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

# Unprivileged. A fixed uid/gid keeps bind-mounted file ownership predictable.
RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --home-dir /app --no-create-home app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/app/.venv/bin:$PATH \
    ENVIRONMENT=production \
    DEBUG=false \
    ALLOW_DEV_AUTH_HEADER=false \
    HOST=0.0.0.0 \
    PORT=8000 \
    WEB_CONCURRENCY=1 \
    RUN_MIGRATIONS=true

WORKDIR /app

COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

# Probes the same endpoint the platform does. urllib is used rather than curl
# so the image needs no apt packages at all; a non-200 raises and exits 1.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/healthz',timeout=4).status==200 or exit(1)"]

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["serve"]
