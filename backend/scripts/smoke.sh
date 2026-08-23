#!/usr/bin/env bash
#
# Boots the real uvicorn server and probes it over HTTP.
#
# Unit and integration tests exercise the app through the ASGI stack in-process;
# this catches what they cannot: import errors at module scope, lifespan
# failures, and a misconfigured host/port binding. It is the same check the
# deployment platform performs against /healthz.
#
# Usage: ./scripts/smoke.sh [port]

set -euo pipefail

PORT="${1:-8123}"
BASE="http://127.0.0.1:${PORT}"
LOG="$(mktemp)"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  echo "--- server log ---" >&2
  cat "$LOG" >&2
  exit 1
}

echo "Starting uvicorn on port ${PORT}..."
uv run --no-sync uvicorn src.main:app --host 127.0.0.1 --port "$PORT" >"$LOG" 2>&1 &
SERVER_PID=$!

# Wait for readiness rather than sleeping a fixed amount.
for _ in $(seq 1 60); do
  if curl -sf "${BASE}/healthz" -o /dev/null 2>/dev/null; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    fail "server exited during startup"
  fi
  sleep 0.5
done

echo "==> GET /healthz returns 200"
STATUS=$(curl -s -o /tmp/healthz.json -w '%{http_code}' "${BASE}/healthz")
[[ "$STATUS" == "200" ]] || fail "expected 200, got ${STATUS}"

echo "==> /healthz payload is well-formed"
uv run --no-sync python - <<'PY' || exit 1
import json
import sys

with open("/tmp/healthz.json") as handle:
    body = json.load(handle)

expected = {"status", "service", "version", "environment", "uptime_seconds", "timestamp"}
if set(body) != expected:
    sys.exit(f"unexpected fields: {sorted(set(body) ^ expected)}")
if body["status"] != "ok":
    sys.exit(f"status is {body['status']!r}, expected 'ok'")
if not isinstance(body["uptime_seconds"], (int, float)) or body["uptime_seconds"] < 0:
    sys.exit(f"bad uptime: {body['uptime_seconds']!r}")

print(f"    status={body['status']} version={body['version']} env={body['environment']}")
PY

echo "==> unknown route returns the standard error envelope"
STATUS=$(curl -s -o /tmp/notfound.json -w '%{http_code}' "${BASE}/definitely-not-a-route")
[[ "$STATUS" == "404" ]] || fail "expected 404, got ${STATUS}"
grep -q '"error"' /tmp/notfound.json || fail "404 body is not the error envelope: $(cat /tmp/notfound.json)"

echo "==> OpenAPI schema is served"
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/openapi.json")
[[ "$STATUS" == "200" ]] || fail "openapi.json returned ${STATUS}"

echo
echo "Smoke test passed."
