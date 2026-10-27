#!/usr/bin/env bash
# Automated end-to-end smoke crossing the three processes:
#   curl → Laravel API (+ queue worker) → Python engine, then Nuxt SSR.
#
# Default run (~1-2 min): register → Bearer token → /api/search through the
# real engine (network: RSS feed, cached after the first run) → Nuxt renders
# the login page (SSR + auth guard). E2E_FULL=1 additionally runs a real
# generate job to completion (downloads audio + ffmpeg — slow).
#
# Env: API_PORT (8000), FRONT_PORT (3000), E2E_FULL (0), E2E_JOB_TIMEOUT (1800s).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8000}"
FRONT_PORT="${FRONT_PORT:-3000}"
API="http://127.0.0.1:${API_PORT}"
FRONT="http://127.0.0.1:${FRONT_PORT}"
LOG_DIR="${TMPDIR:-/tmp}/cortado-e2e"
mkdir -p "$LOG_DIR"

# Each service runs in its own process group (setsid) so cleanup can kill
# the whole tree — killing just the subshell leaves artisan/node orphans.
pids=()
cleanup() {
    for pid in "${pids[@]}"; do kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

say() { printf '\n== %s\n' "$*"; }
fail() { printf 'FAIL: %s (logs in %s)\n' "$*" "$LOG_DIR" >&2; exit 1; }
json() { python3 -c "import sys, json; print(json.load(sys.stdin)$1)"; }

wait_for() { # url expected_code timeout_seconds
    # Accept: application/json matters — without it an unauthenticated
    # Laravel API answers 500 (redirect to an undefined `login` route).
    local url=$1 code=$2 timeout=$3 waited=0
    until [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 -H 'Accept: application/json' "$url" || true)" = "$code" ]; do
        waited=$((waited + 2))
        [ "$waited" -ge "$timeout" ] && fail "$url did not answer $code within ${timeout}s"
        sleep 2
    done
}

say "boot: Laravel on :${API_PORT} + queue worker (engine driver: $(grep '^ENGINE_DRIVER=' "$ROOT/api/.env" | cut -d= -f2))"
(cd "$ROOT/api" && php artisan migrate --force --no-interaction >"$LOG_DIR/migrate.log" 2>&1)
(cd "$ROOT/api" && exec setsid php artisan serve --port="$API_PORT" >"$LOG_DIR/api.log" 2>&1) & pids+=($!)
(cd "$ROOT/api" && exec setsid php artisan queue:work --tries=1 >"$LOG_DIR/queue.log" 2>&1) & pids+=($!)
wait_for "$API/api/user" 401 30

say "auth: register → Bearer token"
EMAIL="smoke-$(date +%s)@example.com"
TOKEN=$(curl -sf -X POST "$API/api/register" \
    -H 'Content-Type: application/json' -H 'Accept: application/json' \
    -d "{\"name\":\"smoke\",\"email\":\"${EMAIL}\",\"password\":\"secret-password\",\"password_confirmation\":\"secret-password\",\"device_name\":\"e2e\"}" \
    | json "['token']")
[ -n "$TOKEN" ] || fail "no token from /api/register"
auth=(-H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' -H 'Content-Type: application/json')

say "search: api → engine round-trip"
SEARCH=$(curl -sf -X POST "$API/api/search" "${auth[@]}" -d '{"query":"marte"}')
COUNT=$(printf '%s' "$SEARCH" | json "['fragments'].__len__()")
[ "$COUNT" -ge 1 ] || fail "search returned no fragments"
echo "   fragments: $COUNT"

if [ "${E2E_FULL:-0}" = "1" ]; then
    FRAGMENT=$(printf '%s' "$SEARCH" | json "['fragments'][0]['id']")
    say "generate job for ${FRAGMENT} (real audio — slow)"
    JOB=$(curl -sf -X POST "$API/api/generate" "${auth[@]}" \
        -d "{\"query\":\"marte\",\"selection\":[\"${FRAGMENT}\"]}" | json "['job']['id']")
    deadline=$(( $(date +%s) + ${E2E_JOB_TIMEOUT:-1800} ))
    while :; do
        STATUS=$(curl -sf "$API/api/jobs/$JOB" "${auth[@]:0:2}" | json "['job']['status']")
        echo "   job $JOB: $STATUS"
        case "$STATUS" in
            done) break ;;
            failed) fail "generate job failed — see $LOG_DIR/queue.log" ;;
        esac
        [ "$(date +%s)" -ge "$deadline" ] && fail "generate job timed out"
        sleep 10
    done
fi

say "boot: Nuxt dev on :${FRONT_PORT} against the API"
(cd "$ROOT/frontend" && NUXT_PUBLIC_API_BASE="$API/api" exec setsid pnpm dev --port "$FRONT_PORT" >"$LOG_DIR/nuxt.log" 2>&1) & pids+=($!)
wait_for "$FRONT/login" 200 180

say "frontend: SSR login page renders (auth guard active)"
curl -sfL "$FRONT/login" | grep -qi password || fail "/login did not render the login form"

say "SMOKE OK — Nuxt(:${FRONT_PORT}) → Laravel(:${API_PORT}) → engine, all answering"
