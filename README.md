# Un cortado, por favor

*tu podcast, a tu gusto.*

> Final project of the *Máster de Desarrollo con IA* (BIG school).
> Technical handle: **`cortado`**. Brand rules in [`docs/branding.md`](docs/branding.md).

## Idea

*Coffee Break: Señal y Ruido* is a Spanish science podcast with ~480 episodes of
~1.5 h each. Every episode has a topic list with timestamps, but finding "what
did they say about black holes?" across ~700 hours of audio is impossible by
hand.

**Un cortado, por favor** turns the catalogue into short, personal audio:

1. You **search** a topic — by keywords or by meaning (semantic AI search: "vida
   extraterrestre" also finds UFOs and Proxima b).
2. You **curate** the suggested fragments (include / exclude / drag to reorder).
3. You **generate** what you want from your selection: a single MP3 with spoken
   announcements, a transcript, a book-style summary, or a **chat** that answers
   questions citing episodes (RAG over the transcripts).

## Features

- Keyword search (accent/case-insensitive, AND) and **semantic search** with an
  optional LLM relevance classifier (keeps/drops each candidate with a reason).
- **Audio clips**: exact ffmpeg cuts concatenated in chronological order, with a
  spoken intro per fragment (podcast, episode number, date), a separating pause
  and a spoken educational disclaimer. Optional split into N-minute blocks.
- **Transcripts** (`.txt` + `.srt`) with faster-whisper, **on demand** and cached
  forever — only for the fragments you pick.
- **RAG chat** about your selection, with sources (episode, date, topic).
- **Book-style summary** (index → chapters → sections) exported to Markdown, and
  to PDF/EPUB when `pandoc` is installed.
- Accounts (register / login / logout) with Laravel Sanctum; every generation
  runs as an **async job** with progress and per-output retry.
- Spanish UI; everything spoken is Spanish too.

## Tech stack

| Layer | Technology |
|---|---|
| `engine/` | Python 3.10+, hexagonal architecture (ports & adapters), ffmpeg, yt-dlp, gTTS, faster-whisper, fastembed (local embeddings), Gemini (optional), pytest |
| `api/` | PHP 8.3, Laravel, Sanctum (SPA cookie + bearer tokens), database queue, Pest |
| `frontend/` | Nuxt 4 (SSR), Vue 3, Nuxt UI 4 + Tailwind, Pinia, Vitest |
| `contract/` | JSON Schema + examples (API ↔ engine) and an OpenAPI spec (frontend ↔ API) |
| CI | GitHub Actions, one path-filtered workflow per subproject |

## Project structure

```
.
├── engine/      Python backend: feed, search, download, ffmpeg, whisper, TTS, RAG, book
├── api/         Laravel API: auth, validation, queued jobs; runs the engine as a subprocess
├── frontend/    Nuxt web UI: search → curate → generate → chat
├── contract/    Versioned JSON contract (schemas + examples) and openapi/
├── docs/        Design notes and the AI development workflow
├── scripts/     dev-up.sh and e2e-smoke.sh (used by the Makefile)
└── Makefile     make up · make test · make e2e-smoke · make e2e-full
```

```
Browser ──► Nuxt (SSR) ──► Laravel API ──stdin/stdout JSON──► Python engine
                               │                                   │
                          queue + jobs                    RSS · ffmpeg · whisper · LLM
```

The engine and the API only talk through [`contract/`](contract/): the API sends
one JSON request on stdin and reads one JSON response from stdout. Each
subproject has its own `README.md` with the details.

## Install and run

Requirements: **PHP 8.3 + Composer**, **Node + pnpm**, **Python 3.10+**, and
**ffmpeg** on the PATH.

```bash
# 1. Engine
cd engine
python3 -m venv .venv && source .venv/bin/activate   # Debian/Ubuntu: sudo apt install python3-venv
pip install -r requirements.txt
cd ..

# 2. API
cd api
composer install
cp .env.example .env && php artisan key:generate
# The API runs the engine with `python3` from the PATH. Point it at the venv from
# step 1 so any terminal works (replace <repo> with the absolute path of this repo):
echo "ENGINE_PYTHON=<repo>/engine/.venv/bin/python" >> .env
touch database/database.sqlite      # SQLite file (migrate fails without it in non-interactive shells)
php artisan migrate --seed          # --seed creates the demo user below (never in production)
cd ..

# 3. Frontend
cd frontend && pnpm install && cd ..

# 4. Run everything (Laravel + queue worker + Nuxt); Ctrl-C stops all
make up
```

Open <http://localhost:3000>. The API runs on `:8000`.

Optional: set `GEMINI_API_KEY` (see [`engine/.env.example`](engine/.env.example))
for semantic classification, chat and book with real answers. With no API key,
search and clip generation still work. No Python/engine at hand? Set
`ENGINE_DRIVER=stub` in `api/.env` to get fixed, contract-shaped responses.

More detail and gotchas: [`docs/local-e2e-setup.md`](docs/local-e2e-setup.md).

### Test account

The app needs a login (every API route is behind Sanctum). After
`php artisan migrate --seed`:

| | |
|---|---|
| **User** | `evaluador@cortado.test` |
| **Password** | `Cortado-2026!` |

Registration is also open at `/register`. These credentials only exist in a
local database seeded by you; they protect nothing real.

### Tests

```bash
make test        # pytest (engine) + Pest (api) + Vitest (frontend)
make e2e-smoke   # register → token → real search → Nuxt SSR login page
```

## Deployment

**Not deployed publicly, on purpose.** The app serves trimmed audio of someone
else's podcast, which is only safe for private, educational use (see the legal
notice below); a public instance would need the authors' permission. It is meant
to run locally with `make up`. Docker is prepared only for the frontend
(`frontend/Dockerfile`); the engine runs as a subprocess of the API on a shared
filesystem, so the API/engine images are the next step in
[`docs/ci-cd-plan.md`](docs/ci-cd-plan.md).

## Problems met and how they were solved

| Problem | Solution |
|---|---|
| ~700 h of audio cannot be transcribed up front | **On-demand transcription**: only the fragments the user curates, cached forever |
| Generating takes minutes; HTTP requests time out | **Async jobs**: `202` + job id, owner-scoped `GET /api/jobs/{id}` polling, separate 30 min job timeout, and a queue `retry_after` that outlasts it |
| Fragment ids collapsed (`Ep563_B` → `ep0`) | Ids keep the episode part and unnumbered episodes get a stable digest; coordinated across engine and API through the inbox |
| A hung ffmpeg / yt-dlp blocked the whole API request | Timeouts on every subprocess; hangs surface as controlled errors |
| Download dropped mid-stream and never fell back | Connection drops raise `NetworkError`, so the yt-dlp fallback actually runs |
| gTTS split the disclaimer mid-phrase (audible broken pause) and speaks slowly | A comma keeps each segment under its 100-char limit, guarded by a test; announcements re-encoded at 1.25× tempo |
| Sanctum cookie auth failed with server-side rendering | The Nuxt `$api` plugin forwards cookie and `referer` on SSR requests |
| API and engine could drift apart | Versioned contract validated by tests on both sides (every example is auto-validated) |
| Google Fonts leaked visitors' IPs | Inter is self-hosted at build time with `@nuxt/fonts` |

## Legal notice

This is an **educational, personal-use** project (final project of the *Máster
de Desarrollo con IA*, BIG school). It is **not affiliated with** *Coffee Break:
Señal y Ruido*, whose audio and feed belong to their authors.

- The tool fetches the public RSS feed and, on demand, downloads episodes to
  cut short fragments for **private listening and study**. Every generated file
  opens with a spoken disclaimer that points listeners to the original source.
- Episodes, clips and transcripts are cached locally and are **never committed**
  to this repository (`engine/cache/` and `engine/output/` are git-ignored).
- Serving trimmed audio to third parties through a **public** web would be
  public communication of someone else's work and would require the podcast's
  permission. The app is therefore designed to run **behind authentication, for
  personal use**. See [`docs/laravel-web.md`](docs/laravel-web.md#6-legal--privacy-decide-before-going-public).
- The source code is released under the [MIT License](LICENSE). The license
  covers the code only, **not** the podcast's audio, feed or trademarks, which
  belong to their authors.
- No API keys or credentials are stored in the repo; use the `.env.example`
  files as templates.
