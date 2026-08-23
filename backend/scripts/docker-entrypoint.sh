#!/bin/sh
#
# Container entrypoint.
#
# Two shapes:
#
#   docker run IMAGE                      -> CMD is "serve": migrate, then uvicorn
#   docker run IMAGE alembic upgrade head -> run that command instead
#
# Anything that is not "serve" is exec'd verbatim, which is what makes one-off
# jobs (migrations, the seed scripts) reuse this image rather than needing
# their own.

set -eu

log() {
  echo "entrypoint: $*" >&2
}

preflight() {
  # A container has no database of its own, but Settings defaults DATABASE_URL
  # to a localhost PostgreSQL. Left unset on the platform, that default turns
  # into `Connect call failed ('127.0.0.1', 5432)` at the bottom of a forty
  # line asyncpg traceback, which names neither the variable nor the fix.
  if [ -z "${DATABASE_URL:-}" ]; then
    log "ERROR: DATABASE_URL is not set."
    log "  Set it in the platform's environment to the pooled connection"
    log "  string, with the postgresql+asyncpg:// driver and no ?sslmode="
    log "  parameter - asyncpg rejects that one and negotiates TLS itself."
    exit 1
  fi

  # Configuration before connectivity: validate_runtime() names the variable
  # that is wrong. Running it here rather than letting the app do it at
  # lifespan means a bad salt is not hidden behind a database timeout.
  python - <<'PREFLIGHT' || exit 1
import sys

from src.core.config import get_settings

problems = get_settings().validate_runtime()
for problem in problems:
    print(f"entrypoint: ERROR: {problem}", file=sys.stderr)
sys.exit(1 if problems else 0)
PREFLIGHT
}

run_migrations() {
  # Alembic owns the schema on PostgreSQL. Doing it here rather than in the
  # application's lifespan keeps a failed migration from being reported as a
  # failed health check, and lets a platform run it as a release command with
  # RUN_MIGRATIONS=false on the web process.
  if [ "${RUN_MIGRATIONS:-true}" != "true" ]; then
    log "RUN_MIGRATIONS is not 'true', skipping alembic"
    return 0
  fi

  log "applying migrations (alembic upgrade head)"
  alembic upgrade head
}

case "${1:-serve}" in
  serve)
    preflight
    run_migrations
    log "starting uvicorn on ${HOST:-0.0.0.0}:${PORT:-8000} with ${WEB_CONCURRENCY:-1} worker(s)"
    # --proxy-headers so client IPs survive the platform's load balancer: the
    # event repository hashes them, and every request would otherwise hash the
    # proxy. --forwarded-allow-ips is deliberately '*' because the only thing
    # in front of this container is that load balancer.
    exec uvicorn src.main:app \
      --host "${HOST:-0.0.0.0}" \
      --port "${PORT:-8000}" \
      --workers "${WEB_CONCURRENCY:-1}" \
      --proxy-headers \
      --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}" \
      --no-server-header
    ;;
  *)
    exec "$@"
    ;;
esac
