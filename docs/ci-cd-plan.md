# CI/CD plan

**Phase 1 (PR gate) is implemented** — see `.github/workflows/{engine,api,frontend}.yml`,
one path-filtered workflow per stack exactly as tabled below (each also
triggers on edits to its own YAML). Phases 2–4 remain future work.

## Tool: GitHub Actions

The repo lives on GitHub and the master teaches GitHub Actions (DevOps & CI/CD
block). No external CI service — keep it simple.

## Architecture: one job per subproject, path-filtered

This is a monorepo with three independent stacks. A change in `frontend/` must
**not** run the Python tests. Use `paths:` triggers (or `dorny/paths-filter`) so
each job runs only when its area changes. This mirrors the repo rule
"one session = one subproject".

| Job | Triggers on changes to | Steps |
|---|---|---|
| `engine` | `engine/**`, `contract/**` | Python 3.10+, **install ffmpeg** (`apt-get install -y ffmpeg`), `pip install -r requirements.txt`, `pytest -q` |
| `api` | `api/**`, `contract/**` | PHP + Composer, `composer install`, `./vendor/bin/pest` |
| `frontend` | `frontend/**` | pnpm (**pinned version**), `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm test`, `pnpm build` |

`contract/**` triggers both `engine` and `api` on purpose: both validate the
contract (`engine/tests/test_contract.py` and
`api/tests/Unit/StubEngineClientTest.php`), so schema drift is caught immediately.

## Project-specific gotchas (these save hours)

- **ffmpeg in CI** — the engine needs it on PATH or the audio/parsing tests fail.
  This is the #1 failure on a fresh runner.
- **pnpm version** — a known risk. Pin it via
  `packageManager` in `package.json` or `version:` in `pnpm/action-setup`, or the
  lockfile won't match.
- **Frozen installs** — use `--frozen-lockfile` (pnpm) / `--no-interaction` so CI
  fails on a stale lockfile instead of regenerating it.
- **Cache** `pip`, Composer and the pnpm store to keep runs fast.

## Phased rollout (don't do it all at once)

1. **Phase 1 — PR gate:** lint + tests per stack with path filters. ~80% of the
   value. Start here.
2. **Phase 2 — quality:** coverage with a threshold (the master suggests 80%) and
   Husky as a local pre-commit gate so we don't rely on CI alone.
3. **Phase 3 — security (free, native):** enable Dependabot and CodeQL / secret
   scanning from repo Settings — named in the master's security block, one click.
4. **Phase 4 — CD:** only when there is something to deploy. The `engine` is a
   local CLI (not deployed); once `api` + `frontend` are ready, build Docker
   images and deploy. Still early.

## Open decisions (owner: project)

- **PHP version** for the `api` job (match local / `composer.json`).
- **Deploy target** for Phase 4 (Vercel / Fly / VPS / …) — not derivable from the
  repo; drives the CD job.
