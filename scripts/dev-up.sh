#!/usr/bin/env bash
# Boot the whole stack for manual browser testing:
# Laravel API + queue worker + Nuxt dev, all torn down on Ctrl-C.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8000}"
FRONT_PORT="${FRONT_PORT:-3000}"

pids=()
cleanup() {
    for pid in "${pids[@]}"; do kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$ROOT/api" && php artisan migrate --force --no-interaction)
(cd "$ROOT/api" && exec setsid php artisan serve --port="$API_PORT") & pids+=($!)
(cd "$ROOT/api" && exec setsid php artisan queue:work --tries=1) & pids+=($!)
(cd "$ROOT/frontend" && NUXT_PUBLIC_API_BASE="http://localhost:${API_PORT}/api" exec setsid pnpm dev --port "$FRONT_PORT") & pids+=($!)

echo
echo "API:      http://localhost:${API_PORT} (engine driver: $(grep '^ENGINE_DRIVER=' "$ROOT/api/.env" | cut -d= -f2))"
echo "Frontend: http://localhost:${FRONT_PORT}"
echo "Ctrl-C stops everything."
wait
