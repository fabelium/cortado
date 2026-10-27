# Decisions & notes

A durable record of choices and context discussed during development that are
not obvious from the code alone. Kept so nothing is lost across a project
restructure. Three parts: **decision log**, **delivery channels**, **AI
providers**, **environment gotchas**.

---

## 1. Decision log (ADR-style)

Short rationale for the non-obvious technical choices.

- **Data source = the public Acast RSS only.** Episode titles, dates, audio URLs
  and the topic list with timestamps all come from one feed; no scraping. The
  audio comes from the `<enclosure>` MP3 URLs the same feed publishes.
- **Download with `requests` (direct), `yt-dlp` as fallback.** Enclosures are
  direct MP3s, so a plain streaming download is simplest; yt-dlp only kicks in
  on a network failure (handles awkward CDNs).
- **Cut & concat by re-encoding to a uniform MP3** (44.1 kHz / stereo / 192 kbps)
  rather than stream-copy. Re-encoding gives sample-accurate cuts and glitch-free
  concatenation across episodes with different encodings.
- **Parser uses time-anchors, not separators.** Descriptions are wildly
  irregular (one line or many; `;` or bullets; `Cara A:` prefixes; inner parens
  and hyphens in names; `mm:ss` / `h:mm:ss` / `(min m:ss)`). The robust approach
  is to treat each timestamp as an anchor and take the text between anchors as a
  topic name — this is why it jumped from 27 to 481 episodes parsed.
- **Search = keyword (AND, accent/case-insensitive) + optional semantic.** The
  keyword strategy is the default; semantic search (embeddings) is opt-in via
  `--semantic`. Both implement the same `SearchStrategy` port.
- **Chronological order is owned by the assembler, not the search.** Semantic
  search returns results ranked by relevance (for display); the `ClipAssembler`
  sorts by date so the *audio* is always chronological regardless of strategy.
- **No fine-tuning for chat/book — use RAG.** "Train a model on the podcast" is
  the wrong/expensive framing; the right one is retrieval + an LLM citing episode
  and minute. (See `docs/laravel-web.md` and TODO ideas 2–3.)
- **Embeddings are cached on disk** (`cache/embeddings/*.npz`) so the ~2,000
  topics are embedded once; re-runs are instant.
- **AI providers are pluggable and selectable** (`EmbeddingProvider`/`ChatModel`
  ports + `ProviderFactory`). Default is **local & free** (fastembed); APIs are
  opt-in via a key. No vendor SDK is required for Gemini (REST via `requests`).
- **Redis/queues belong to the future web layer, not the engine.** `ClipService`
  is stateless and queue-friendly on purpose; the engine stays free of Redis.

## 2. Delivery channels (how the result reaches the user)

- **E-mail — DONE.** `--email` via SMTP, credentials from env, 24 MB guard.
  This is the clean, automatable channel.
- **WhatsApp — NOT feasible to automate.** There is no official API for *personal*
  accounts. Options are the WhatsApp **Cloud API** (business-only: number
  registration, message templates, verification — overkill to message yourself)
  or **unofficial** libraries that automate WhatsApp Web (against the ToS, risk of
  number ban). Conclusion: do it **manually** (attach the file as a document), or
  use Telegram instead. No code was added for WhatsApp.
- **Telegram — recommended future channel.** The **Telegram Bot API** is official,
  free and trivial: one `requests.post` with a `bot_token` + `chat_id` sends the
  MP3. Good candidate for a `--telegram` flag (mirrors the `--email` design). Not
  built yet — see TODO/ACTIONS minor improvements.

## 3. AI providers (free options surveyed)

The engine can use a **local model or an API**, selectable per run. Survey as of
mid-2026 — useful when adding more provider adapters:

| Provider | Free? | Embeddings | Chat/LLM | Notes |
|----------|-------|-----------|----------|-------|
| **Local** (fastembed / Ollama) | ✅ fully, offline | fastembed (ONNX, light) | Ollama | No key, private. **Current default for embeddings.** |
| **Google Gemini** | ✅ generous free tier | `text-embedding-004` | Gemini Flash | Best free API; only needs a Google key. **Wired.** |
| **Mistral** | ✅ free tier | `mistral-embed` | Mistral models | Free key on the platform. *(future adapter)* |
| **Cohere** | ✅ trial key | multilingual + rerank | Command | Strong multilingual + reranking. *(future adapter)* |
| **Groq** | ✅ free tier | ❌ | very fast LLMs | Chat only, no embeddings. *(future adapter)* |
| **Anthropic (Claude)** | ❌ paid | ❌ | Claude | Best quality, but no free tier. |

Wired today: **local (fastembed)** + **Gemini** (embeddings & chat). Mistral,
Cohere, Groq are natural next adapters behind the same ports (one branch each in
`ProviderFactory`). Keys read from `GEMINI_API_KEY` / `GOOGLE_API_KEY`.

## 4. Environment gotchas (this machine)

- **ffmpeg** was not installed initially; installed via `sudo apt install ffmpeg`
  (needs a real terminal for the sudo password — it cannot run from inside the
  agent sandbox). `ffmpeg` + `ffprobe` are both required.
- **PEP 668 / externally-managed environment.** Plain `pip install` is blocked.
  Either create a venv (`sudo apt install python3.12-venv` first) or use
  `pip install --user --break-system-packages` (fine on a personal machine).
- **Python 3.12** here; the tool targets 3.10+.
- The `click` version warning from gTTS is harmless (the library does not use
  click; only its CLI does).
