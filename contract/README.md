# contract — engine ↔ API JSON protocol (v1.0)

The versioned seam between the Laravel `api/` and the Python `engine/`. The
engine reads one JSON request on stdin and writes one JSON response on stdout;
the API never parses console text. Both sides validate against the schemas here.

**Engine side: implemented.** `engine/engine.py` honours this contract — all
five actions work: `search`, `generate`, `transcribe`, `chat` and `book`. Try it:

```bash
cd engine && echo '{"version":"1.0","action":"search","query":"marte",
                    "options":{"limit":5}}' | python3 engine.py
```

## Seams

- **API ↔ engine (this directory):** `schema/` + `examples/`, version `1.0`.
- **Nuxt ↔ API:** `openapi/openapi.yaml` — REST/OpenAPI 3.1 spec of the public
  Laravel surface (Sanctum auth in both flavours, sync `search`/`chat`, queued
  `generate`/`transcribe`/`book` + `GET /api/jobs/{id}` polling).

## Request

`schema/request.schema.json`. Every request carries `version: "1.0"` and an
`action`. Frozen actions: `search`, `generate`, `transcribe`, `chat`, `book`
(none reserved — every action has a frozen response schema).

## Responses

One schema per action: `response.search.schema.json`,
`response.generate.schema.json`, `response.transcribe.schema.json`,
`response.chat.schema.json`, `response.book.schema.json`, and
`response.error.schema.json` for failures. Success responses set `ok: true`;
errors set `ok: false` with `error` and `code`.

## Exit codes

`0` ok · `1` controlled error · `130` interrupted. The error enum also keeps
`2` (generated but delivery failed), reserved for the human CLI's e-mail flow —
the JSON entry point never emits it.

## Examples

`examples/` holds request→response pairs the frontend/API can mock against:

- `search.request.json` / `search.response.json` — a basic search.
- `search.tuned.request.json` — semantic search with `classify`, `top_k` and
  `threshold`; `search.classified.response.json` — a realistic multi-fragment
  result with cosine `score`s and Spanish `reason`s (what `classify` yields).
- `generate.*`, `transcribe.*`, `chat.*`, `book.*` — the other actions.
- `error.response.json` (controlled error, code `1`) and
  `error.interrupted.response.json` (interruption, code `130`).

The response fields `score` (cosine similarity) and `reason` (LLM relevance
justification) are `null` for keyword search and populated by semantic search /
`classify`.

## Validation

`engine/tests/test_contract.py` validates every file in `examples/` against its
schema (needs `jsonschema`, in `engine/requirements.txt`):

    cd engine && python3 -m pytest tests/test_contract.py -q
