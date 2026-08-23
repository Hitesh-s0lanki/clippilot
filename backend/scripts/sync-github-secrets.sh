#!/usr/bin/env bash
#
# Pushes the values in backend/.env to the repository's GitHub Actions
# secrets and variables, so .github/workflows/backend-docker.yml has the
# configuration it needs.
#
#   ./scripts/sync-github-secrets.sh --dry-run     # names only, nothing sent
#   ./scripts/sync-github-secrets.sh               # push
#   ./scripts/sync-github-secrets.sh path/to/.env  # a different source file
#   ./scripts/sync-github-secrets.sh --database-url  # prompt for it instead
#
# --database-url takes the deployment database from a silent prompt rather than
# from .env, so it stays out of the shell history and the process list. Use it
# when .env holds the SQLite URL for local work, which is the normal case.
#
# The split is deliberate: a credential becomes a *secret* (write-only, masked
# in every log), and everything else becomes a *variable* (readable in the
# Actions UI, which is what you want for a bucket name you will need to check).
# Nothing here ever prints a value.
#
# Requires the gh CLI, authenticated with admin rights on the repository.

set -euo pipefail

DRY_RUN=false
PROMPT_DB_URL=false
ENV_FILE=".env"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --database-url) PROMPT_DB_URL=true ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *) ENV_FILE="$arg" ;;
  esac
done

SECRET_KEYS=(
  DATABASE_URL
  IP_HASH_SALT
  ANTHROPIC_API_KEY
  OPENAI_API_KEY
  FIRECRAWL_API_KEY
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
)

VARIABLE_KEYS=(
  CLERK_JWKS_URL
  CLERK_ISSUER
  CLERK_AUDIENCE
  CORS_ORIGINS
  S3_BUCKET
  S3_REGION
  S3_KEY_PREFIX
  S3_PUBLIC_BASE_URL
  AGENT_PROVIDER
  AGENT_MODEL
  FIRECRAWL_MCP_URL
)

if [[ ! -f "$ENV_FILE" ]]; then
  echo "No such file: $ENV_FILE" >&2
  exit 1
fi

command -v gh >/dev/null || { echo "gh is not installed: https://cli.github.com" >&2; exit 1; }

REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
echo "Repository: $REPO"
echo "Source:     $ENV_FILE"
$DRY_RUN && echo "Mode:       dry run, nothing will be sent"
echo

# Reads one key without letting its value reach stdout or the process list.
read_value() {
  local key="$1" line
  line="$(grep -m1 -E "^${key}=" "$ENV_FILE" || true)"
  line="${line#*=}"
  line="${line%\"}"; line="${line#\"}"
  line="${line%\'}"; line="${line#\'}"
  printf '%s' "$line"
}

# Values that are placeholders rather than configuration. Pushing one is worse
# than pushing nothing: the workflow then looks configured and is not.
warn_if_placeholder() {
  local key="$1" value="$2"
  case "$key" in
    IP_HASH_SALT)
      if [[ "$value" == "dev-only-change-me" ]]; then
        echo "  !! IP_HASH_SALT is still the placeholder. Generate one with:"
        echo "     python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
        return 1
      fi
      ;;
    DATABASE_URL)
      if [[ "$value" == sqlite* ]]; then
        echo "  !! DATABASE_URL points at SQLite. The deployment target is"
        echo "     PostgreSQL - set the pooled postgresql+asyncpg:// URL instead."
        return 1
      fi
      ;;
  esac
  return 0
}

# Neon, Supabase and RDS all hand out a URL that asyncpg cannot use verbatim.
# Two things have to change, and both are silent failures if they do not:
# the driver has to be named (SQLAlchemy defaults postgresql:// to psycopg2,
# which is not installed), and sslmode/channel_binding have to go (asyncpg
# raises `invalid connection option` rather than ignoring them - it negotiates
# TLS on its own).
normalise_pg_url() {
  DB_URL_RAW="$1" python3 - <<'NORMALISE'
import os
import sys
import urllib.parse

raw = os.environ["DB_URL_RAW"].strip()
parts = urllib.parse.urlsplit(raw)

scheme = parts.scheme
if scheme in ("postgres", "postgresql"):
    scheme = "postgresql+asyncpg"
elif scheme != "postgresql+asyncpg":
    sys.exit(f"!! not a PostgreSQL URL: scheme is {parts.scheme!r}")

dropped = []
kept = []
for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=True):
    if key in ("sslmode", "channel_binding", "options"):
        dropped.append(key)
    else:
        kept.append((key, value))

notes = []
if dropped:
    notes.append("dropped " + ", ".join(dropped) + " (asyncpg rejects them)")
if parts.scheme != scheme:
    notes.append(f"driver {parts.scheme} -> {scheme}")
host = parts.hostname or ""
if "neon.tech" in host and "-pooler" not in host:
    notes.append("WARNING: this is the direct endpoint, not the pooled one")

print(urllib.parse.urlunsplit((scheme, parts.netloc, parts.path,
                               urllib.parse.urlencode(kept), parts.fragment)))
for note in notes:
    print(note, file=sys.stderr)
NORMALISE
}

skipped=()

push() {
  local kind="$1" key="$2" value
  if [[ "$key" == "DATABASE_URL" && "$PROMPT_DB_URL" == true ]]; then
    value="$PROMPTED_DB_URL"
  else
    value="$(read_value "$key")"
  fi

  if [[ -z "$value" ]]; then
    printf '  %-8s %-24s skipped, empty in %s\n' "$kind" "$key" "$ENV_FILE"
    skipped+=("$key")
    return
  fi

  if ! warn_if_placeholder "$key" "$value"; then
    printf '  %-8s %-24s skipped, see above\n' "$kind" "$key"
    skipped+=("$key")
    return
  fi

  if $DRY_RUN; then
    printf '  %-8s %-24s would be set (%d chars)\n' "$kind" "$key" "${#value}"
    return
  fi

  if [[ "$kind" == "secret" ]]; then
    printf '%s' "$value" | gh secret set "$key" --repo "$REPO"
  else
    gh variable set "$key" --repo "$REPO" --body "$value"
  fi
  printf '  %-8s %-24s set\n' "$kind" "$key"
}

PROMPTED_DB_URL=""
if $PROMPT_DB_URL; then
  # -s so it never reaches the terminal or the history file.
  read -rsp 'Deployment database URL (input hidden): ' entered
  echo
  if [[ -z "$entered" ]]; then
    echo "Nothing entered; falling back to $ENV_FILE for DATABASE_URL."
    PROMPT_DB_URL=false
  else
    PROMPTED_DB_URL="$(normalise_pg_url "$entered")" || exit 1
    echo "  normalised (${#PROMPTED_DB_URL} chars, value not shown)"
    echo
  fi
fi

echo "Secrets"
for key in "${SECRET_KEYS[@]}"; do push secret "$key"; done

echo
echo "Variables"
for key in "${VARIABLE_KEYS[@]}"; do push variable "$key"; done

echo
if [[ ${#skipped[@]} -gt 0 ]]; then
  echo "Not set: ${skipped[*]}"
  echo "The workflow falls back to a safe default for each of these, so it stays"
  echo "green - but production needs them filled in."
  echo
fi
echo "RENDER_DEPLOY_HOOK_URL is not in .env. Set it by hand to enable the deploy"
echo "step; without it the workflow builds and verifies, then stops:"
echo "  gh secret set RENDER_DEPLOY_HOOK_URL --repo $REPO"
