# Local end-to-end setup

How to run the whole stack locally (Nuxt → Laravel API → Python engine) and
smoke-test it. Originally written when the frontend was mock-backed; since
2026-07-02 the cutover is done — the frontend talks to Laravel by default,
auth (Sanctum SPA cookie) is live, and the heavy actions run as queued jobs.

## One-command bring-up

From the repo root (see `Makefile` / `scripts/`):

```bash
make up                    # Laravel + queue worker + Nuxt dev; Ctrl-C stops all
make e2e-smoke             # automated smoke: register → token → search via the
                           # real engine → Nuxt SSR login page (~1-2 min)
make e2e-full              # smoke + a real generate job to completion (slow:
                           # downloads audio + ffmpeg)
make test                  # the three unit-test suites (pytest / pest / vitest)
```

`API_PORT` / `FRONT_PORT` override the defaults (8000 / 3000). Smoke logs land
in `$TMPDIR/cortado-e2e/`. Note: the engine runs as a **subprocess of the API**
(shared filesystem), so local bring-up is host processes; Docker images belong
to the CD phase of `docs/ci-cd-plan.md`.

## Status per layer

| Layer | State |
|---|---|
| **API** (`api/`) | ✅ all five actions + auth + async jobs (`GET /api/jobs/{id}`) |
| **Nuxt** (`frontend/`) | ✅ real API by default, login/register UI, job polling |
| **Engine** (`engine/`) | ✅ `ENGINE_DRIVER=subprocess` is the API default |

The public REST seam is specified in `contract/openapi/openapi.yaml`.

## Requirements on the host

- PHP 8.3+ + Composer (`cd api && composer install`), first run:
  `cp .env.example .env && php artisan key:generate && php artisan migrate`.
- Node + pnpm (`cd frontend && pnpm install`).
- Python 3.10+ + `pip install -r engine/requirements.txt` **and ffmpeg on PATH**
  (needed by `generate`; searches only need the RSS feed / its cache).
- Optional for semantic/chat/book: `GEMINI_API_KEY` in the engine environment
  (see `engine/.env.example`); `stub` driver works with none of this
  (`ENGINE_DRIVER=stub` in `api/.env`).

## Gotchas

- Auth endpoints are throttled (5 req/min per IP) — manual retry loops will 429.
- Unauthenticated `/api/*` requests need `Accept: application/json` to get a
  clean 401 (otherwise Laravel tries to redirect to a `login` web route).
- Sanctum's stateful check needs origin/referer from `SANCTUM_STATEFUL_DOMAINS`
  (`localhost:3000` by default) — the Nuxt `$api` plugin forwards both in SSR.
- `generate`/`transcribe`/`book` need the queue worker running; without it jobs
  stay `queued` forever.
