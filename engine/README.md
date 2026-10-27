# Coffee Clips

A local command-line tool that searches a topic in the podcast
**Coffee Break: Señal y Ruido** and builds a single MP3 with all the fragments
from the episodes where that topic was discussed, in chronological order.

It reads the topics and their timestamps from the public
[Acast RSS feed](https://feeds.acast.com/public/shows/coffee-break-senal-y-ruido).
Strictly private use: there is no server and no file distribution.

The generated **audio content stays in Spanish** (the podcast is Spanish: the
spoken announcements, the educational disclaimer and the dates are read aloud to
a Spanish-speaking audience). The **code, comments and docs are in English**.

## Requirements

- Python 3.10+
- **ffmpeg** on the PATH (`sudo apt install ffmpeg` on Linux, `brew install ffmpeg` on macOS)
- Python dependencies: `feedparser`, `requests`, `yt-dlp`, `gTTS`, `faster-whisper`

## Installation

Recommended (virtual environment):

```bash
cd cortado/engine
python3 -m venv .venv         # on Debian/Ubuntu: sudo apt install python3-venv
source .venv/bin/activate
pip install -r requirements.txt
```

Quick alternative without a venv (personal machine):

```bash
pip install --user -r requirements.txt   # add --break-system-packages if pip asks for it
```

## Usage

```bash
python3 coffee_clips.py "agujero negro"        # search, show and ask for confirmation
python3 coffee_clips.py "marte" --limit 10     # at most 10 fragments
python3 coffee_clips.py "materia oscura" --yes # no confirmation
python3 coffee_clips.py --refresh "exoplaneta" # force a feed re-download
```

With no arguments, it asks for the term interactively.

### Options

| Option           | Effect                                                          |
|------------------|----------------------------------------------------------------|
| `--semantic`     | AI semantic search (embeddings) instead of keyword matching.   |
| `--model NAME`   | Embedding provider for `--semantic`: `local` (default) / `gemini`. |
| `--classify`     | With `--semantic`, let an LLM judge each candidate's relevance. |
| `--limit N`      | Use at most the first N fragments (most relevant under `--semantic`). |
| `--yes`, `-y`    | Do not ask for confirmation before generating.                |
| `--refresh`      | Ignore the feed cache and download it again.                  |
| `--no-intro`     | Do not add the announcement (episode + date) before each fragment. |
| `--no-disclaimer`| Do not add the spoken educational disclaimer at the start.    |
| `--split MIN`    | Split the output into blocks of <= MIN minutes (whole fragments). |
| `--transcript`   | Transcribe the generated audio to `.txt` and `.srt`.          |
| `--email [ADDR]` | E-mail the MP3 when done (see below).                         |
| `--keep-temp`    | Keep the temporary fragments (for debugging).                |
| `--output PATH`  | Output MP3 path.                                              |
| `--clean-cache`  | Delete the cache (feed + episodes) and exit.                 |

Downloading uses `requests` directly and, if an episode fails over the
network/CDN, it automatically falls back to `yt-dlp`.

### Announcements (voice)

By default, a Spanish announcement (generated with gTTS) is inserted before each
fragment stating the episode number and the date, e.g.
*"Episodio 237. 17 de octubre de 2019."*. Disable it with `--no-intro`. An
educational disclaimer is also spoken at the start of each file unless you pass
`--no-disclaimer`.

### AI semantic search

`--semantic` finds topics by *meaning*, not just words, so "agujeros negros"
also surfaces related segments (e.g. "Sgr A*", "primordial black holes as dark
matter candidates"). It embeds every topic name once and caches the vectors on
disk (`cache/embeddings/`), so only new episodes are ever embedded.

```bash
python3 coffee_clips.py "vida extraterrestre" --semantic
python3 coffee_clips.py "materia oscura" --semantic --classify   # + LLM relevance filter
python3 coffee_clips.py "agujeros negros" --semantic --model gemini
```

The provider is selectable. The default `local` backend (fastembed, multilingual
MiniLM) is free and offline — no API key. `--model gemini` and `--classify` use
the Gemini API (free tier); set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) to enable
them. Results are shown ranked by relevance; the generated audio is always
chronological.

### Blocks for long audios

With many fragments the audio can run for hours. `--split 30` (or `--split 60`)
groups **whole fragments** into blocks not exceeding that duration and produces
several files `..._parte1.mp3`, `..._parte2.mp3`, ... A fragment longer than the
limit forms its own block (it is never cut in half).

### E-mail delivery

`--email` sends the result when done. Credentials are read from environment
variables (never hard-coded); for Gmail you need an *app password*:

```bash
export COFFEE_SMTP_USER="you@gmail.com"
export COFFEE_SMTP_PASS="xxxx xxxx xxxx xxxx"   # app password
export COFFEE_MAIL_TO="dest@example.com"        # optional; defaults to yourself
python3 coffee_clips.py "marte" --limit 5 --yes --email
```

Supported variables: `COFFEE_SMTP_USER`, `COFFEE_SMTP_PASS`, `COFFEE_MAIL_TO`,
`COFFEE_SMTP_HOST` (default `smtp.gmail.com`), `COFFEE_SMTP_PORT` (default `587`).
Attachment limit: 24 MB (use `--split` or `--limit` if you exceed it).

## How it works

1. **Feed** — downloads and parses the RSS (`coffee/feed/`, `coffee/parsing/`).
   The parser tolerates the irregular description format: topics on one line or
   several, separated by `;` or bullets, with inner parentheses and hyphens in
   the names, and times `mm:ss` / `h:mm:ss` / `(min m:ss)`.
2. **Search** — case- and accent-insensitive; requires *all* the query words in
   the topic name (`coffee/search/`).
3. **Confirmation** — shows the fragment table and the estimated duration.
4. **Audio** — downloads only the required episodes, cuts each fragment with
   ffmpeg (uniform re-encode) and concatenates them (`coffee/application/`,
   `coffee/infrastructure/ffmpeg.py`).
5. **Output** — `output/<term>_<date>.mp3`. Temporary fragments are deleted; the
   full episode MP3s remain in `cache/episodes/` for future searches.

## JSON entry point (for the API)

`coffee_clips.py` is the human CLI. `engine.py` is the machine-facing sibling
the Laravel API calls: it reads ONE JSON request from **stdin** and writes ONE
JSON response to **stdout** (progress goes to stderr, so stdout is pure JSON).
Both sides validate against the frozen contract in [`../contract/`](../contract).

```bash
# search
echo '{"version":"1.0","action":"search","query":"agujeros negros",
       "options":{"semantic":true,"model":"local","limit":10}}' | python3 engine.py

# generate (selection ids come from a previous search response)
echo '{"version":"1.0","action":"generate","query":"agujeros negros",
       "selection":["ep237@2340-2880"],"options":{"intro":true,"split":30}}' | python3 engine.py
```

Semantic search accepts tuning in `options`: `top_k` (max candidates) and
`threshold` (minimum cosine similarity, 0..1); both fall back to the settings
defaults. The human CLI exposes them as `--top-k` and `--threshold`.

Actions: all five contract actions are implemented — `search`, `generate`,
`transcribe`, `chat` (RAG over fragment transcripts) and `book` (outline →
sections → Markdown/pandoc). Exit codes: `0` ok · `1` controlled error · `130`
interrupted (code `2`, delivery failed, belongs to the human CLI's `--email`
flow; the JSON entry point never emits it).
Fragment ids have the form `ep<key>@<start>-<end>` — the key is the
episode number plus the part letter for split episodes (`ep563b`), or a stable
guid digest for unnumbered ones (`epx3fa2c81`) — and round-trip between `search`
results and `generate` selections.

## Architecture

The codebase follows a **hexagonal (ports & adapters)** layout. Each module
docstring names the design pattern it embodies. Dependencies are injected
through constructors and wired in a single composition root (`coffee/cli.py`),
so the core never depends on concrete infrastructure.

```
engine/
├── coffee_clips.py               # 2-line shim -> coffee.cli:main (human CLI)
├── engine.py                     # stdin-JSON -> stdout-JSON entry point (API-facing)
├── coffee/
│   ├── config.py                 # immutable Settings (env overrides)
│   ├── cli.py                    # argparse + composition root (Dependency Injection)
│   ├── domain/
│   │   ├── models.py             # frozen value objects: TimeRange/Topic/Episode/Fragment
│   │   └── errors.py             # CoffeeError hierarchy
│   ├── parsing/
│   │   └── description_parser.py # DescriptionParser: text -> Topics (pure)
│   ├── infrastructure/
│   │   ├── http_client.py        # HttpClient: requests.Session + retries/backoff
│   │   ├── ffmpeg.py             # FFmpeg adapter: cut/encode/silence/probe/concat
│   │   ├── json_cache.py         # JsonCache: feed cache (24 h) + episode MP3 cache
│   │   ├── embedding_cache.py    # persisted embeddings, keyed by model+text
│   │   └── pandoc.py             # PandocExporter: Markdown -> PDF/EPUB (degrades)
│   ├── feed/
│   │   ├── feed_source.py        # FeedSource: RSS -> domain Episodes
│   │   └── episode_repository.py # EpisodeRepository (Repository pattern)
│   ├── search/
│   │   ├── search_strategy.py    # SearchStrategy port + KeywordSearchStrategy (Strategy)
│   │   ├── semantic_search_strategy.py # embeddings + optional LLM classification
│   │   ├── search_service.py     # SearchService (Strategy client)
│   │   └── text.py               # accent/case normalization
│   ├── audio/
│   │   └── downloader.py         # AudioDownloader port; Http/YtDlp adapters; Fallback (Chain)
│   ├── speech/
│   │   ├── text_to_speech.py     # TextToSpeech port + GttsTextToSpeech adapter
│   │   ├── transcriber.py        # Transcriber port + FasterWhisperTranscriber adapter
│   │   └── announcements.py      # AnnouncementBuilder: Spanish announcement + date
│   ├── ai/                       # embedding/chat providers (fastembed, Gemini) +
│   │   └── ...                   # ProviderFactory, RelevanceClassifier
│   ├── knowledge/                # RAG + book: transcript store/chunker/retriever,
│   │   └── ...                   # RagService, outline/sections, MarkdownRenderer
│   ├── delivery/
│   │   └── email_sender.py       # EmailSender adapter (SMTP)
│   └── application/
│       ├── fragment_ref.py       # fragment ids: to_id / build_index / resolve
│       ├── clip_assembler.py     # ClipAssembler: download/cut/pack/concat (DI)
│       └── clip_service.py       # ClipService: end-to-end use case (Facade)
├── tests/                        # one file per unit; each runs standalone and under pytest
├── requirements.txt
└── README.md
```

### Design patterns at a glance

- **Ports & Adapters (hexagonal):** abstract ports (`AudioDownloader`,
  `TextToSpeech`, `Transcriber`, `SearchStrategy`) with concrete adapters; the
  application core depends only on the ports.
- **Repository:** `EpisodeRepository` hides cache-vs-feed behind one method.
- **Strategy:** `SearchStrategy` with two adapters, `KeywordSearchStrategy`
  and `SemanticSearchStrategy` (embeddings + optional LLM classification).
- **Chain of responsibility:** `FallbackDownloader` (HTTP first, yt-dlp on
  `NetworkError`).
- **Facade:** `ClipService` orchestrates the whole use case; stateless and
  queue-friendly for a future async worker.
- **Dependency Injection:** every collaborator is passed through constructors;
  the only wiring point is `coffee/cli.py`.

## Cache

- `cache/feed_cache.json` — parsed feed; re-downloaded after 24 h.
- `cache/episodes/*.mp3` — full episodes, reused across searches.

Delete the `cache/` folder to start fresh.

## Tests

```bash
python3 tests/test_parsing.py          # or: python3 -m pytest tests/ -q
python3 tests/test_mailer.py
```

Both test files run standalone and under pytest.
