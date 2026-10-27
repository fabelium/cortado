# Web layer (Laravel) — design notes

Everything we discussed about the future web front end, captured so nothing is
lost. This is a **planning document**, not built yet. It will be developed in a
**separate working session** from the Python engine; the two connect through a
stable contract (see below).

> Status: NOT STARTED. The Python engine (this repo) is the backend it will
> drive.

---

## 1. Vision

A web app where the user does not type flags but *curates*. The desired flow:

1. **Configure the podcast / pick a topic** — the user enters a topic of interest.
2. **AI proposes** — the engine suggests related segments (semantic search), each
   with episode, date, minute and a relevance score/reason.
3. **The user curates** — includes/excludes suggestions, and can **reorder** them
   if they prefer a non-chronological arrangement.
4. **The user picks outputs** — for the curated selection, choose any of:
   - concatenated **audio** (with the spoken intro/disclaimer already built),
   - **transcript**,
   - **book-style summary** (index + chapters),
   - **chat** (RAG) about the selected material.
5. **Generate** — a button kicks off the work; the user sees **live progress**
   and gets the artifacts when ready.

The point: the AI does the *finding and classifying*, the human keeps *editorial
control* (what goes in, in which order), and the engine does the *heavy lifting*.

---

## 2. Architecture (layers)

```
┌─────────────────────────────────────────────────────────┐
│  Laravel (web)  — UI, users, auth, job queue, chat UI     │
│   topic → AI suggests → curate/reorder → pick outputs →   │
│   generate (with live progress)                           │
└───────────────┬─────────────────────────────────────────┘
                │  async jobs + progress over websockets (Reverb)
┌───────────────▼─────────────────────────────────────────┐
│  Python engine (this repo)  — the heavy work              │
│   feed · search · download · ffmpeg · whisper · TTS · RAG │
└───────────────┬─────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────┐
│  Knowledge layer  — embeddings + vector store + LLM       │
│   (already started: EmbeddingProvider / ChatModel ports)  │
└─────────────────────────────────────────────────────────┘
```

The engine's `ClipService` was deliberately written **stateless and
queue-friendly** precisely so a Laravel worker can drive it without changes.

---

## 3. Laravel ↔ Python engine: the contract

Two integration options (decide when we start):

- **A — CLI / subprocess.** A Laravel queued Job shells out to `coffee_clips.py`
  (or a small `engine` CLI) and reads JSON from stdout. Simplest; good first step.
- **B — FastAPI microservice.** Wrap the engine in an HTTP service Laravel calls.
  Cleaner if it needs to scale or run on a separate (GPU) box.

**Recommendation:** start with **A** (subprocess) for the master's project, keep
the door open to **B**. Either way, the engine must expose a **stable contract**:

- **Input:** a JSON request — `{ "action": "search|generate|transcribe|book|chat",
  "query": "...", "selection": [fragment ids], "options": { intro, disclaimer,
  split, model, classify, ... } }`.
- **Output:** structured JSON — for `search`, the ranked fragments (episode, date,
  start/end, duration, score, reason); for `generate`, the produced file paths +
  durations; errors as `{ "error": "...", "code": N }`.
- **Exit codes (already defined in the CLI):** `0` ok · `1` controlled error ·
  `2` generated but delivery (e-mail) failed · `130` interrupted.
- **Progress:** the engine already emits human-readable progress lines via a
  `report` callback; for the web we expose them as structured events the Job can
  forward to the browser.

**Action item (Milestone 5):** before writing Laravel, add a thin `engine`
entry point that speaks JSON in/out, so the web never parses console text.

---

## 4. Async / jobs

Generating is slow (downloads + ffmpeg + whisper), so **nothing runs in the
request cycle**:

- Laravel **Queue + Jobs** (Redis-backed) per generation request.
- **Progress in real time** via **Laravel Reverb** (websockets): the Job streams
  percentage / step messages the engine reports.
- **Redis** also fits: rate limiting, caching search results, and as the queue
  backend. (Redis belongs to THIS web layer — the Python engine stays free of it.)
- Idempotency / resumability: a generated artifact is cached by (selection +
  options) hash so re-requests are instant.

---

## 5. Data model (sketch)

- `users` — auth/ownership.
- `podcasts` — feed URL + metadata (multi-podcast ready).
- `topics` / `segments` — parsed from the feed (episode, date, time range, name,
  embedding ref).
- `selections` — a user's curated set for a query (ordered, include/exclude).
- `artifacts` — generated outputs (audio / transcript / book / chat session),
  with status (queued/running/done/failed), file path, duration, options hash.
- `jobs` — queue bookkeeping (Laravel's own tables).

---

## 6. Legal / privacy (decide before going public)

- Private/educational use (single user, behind login) = safe ground.
- A **public** web that serves the trimmed audio to third parties would be
  public communication of someone else's work → it would need the **podcast's
  permission**. This conditions the whole design.
- Keep the disclaimer; keep the original-source recommendation; likely keep the
  app **behind authentication** and personal.

---

## 7. Open decisions (to settle when we start Milestone 5)

- Integration style: subprocess CLI (A) vs FastAPI (B). *Lean A first.*
- Where the engine runs: same host as Laravel vs separate worker/box.
- Whether transcripts/embeddings live in the Python cache, in Redis, or in the
  DB (Postgres + pgvector is an option for the knowledge layer).
- Auth/visibility: strictly single-user vs multi-user private.
- How much of the Python cache (episode MP3s, vectors) the web reuses directly.

---

## 8. Working agreement

- The **engine** (Python, this repo) and the **web** (Laravel) are built in
  **separate sessions** to keep each context focused.
- The seam between them is the **JSON contract** in §3. As long as both sides
  honour it, they can evolve independently.
- Next concrete step for the web: **define and freeze that contract** (a small
  `engine` JSON entry point on the Python side), then scaffold Laravel against it.
