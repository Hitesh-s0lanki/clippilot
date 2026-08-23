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
