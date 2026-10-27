#!/usr/bin/env python3
"""JSON-in / JSON-out entry point for the Laravel API (contract v1.0).

This is the machine-facing sibling of ``coffee_clips.py`` (the human CLI). It
reads ONE JSON request from stdin, validates it against the frozen contract
(``../contract/schema``), runs the use case through ``ClipService`` and writes
ONE JSON response to stdout. Progress goes to stderr so stdout stays pure JSON
that the API can parse without guessing.

Actions: ``search``, ``generate``, ``transcribe``, ``chat`` and ``book`` are
implemented.

Exit codes (contract): 0 ok · 1 controlled error · 2 generated but delivery
failed · 130 interrupted.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coffee.application.fragment_ref import resolve, to_id
from coffee.cli import build_book_composer, build_rag_service, build_search_service, build_service, slugify
from coffee.config import Settings
from coffee.domain.errors import CoffeeError
from coffee.domain.models import SearchHit
from coffee.infrastructure.ffmpeg import FFmpeg
from coffee.infrastructure.pandoc import PandocExporter
from coffee.knowledge.markdown_renderer import MarkdownRenderer
from coffee.knowledge.rag_answerer import RagAnswer
from coffee.speech.announcements import episode_number
from coffee.speech.transcriber import FasterWhisperTranscriber

CONTRACT_VERSION = "1.0"
_CONTRACT_DIR = Path(__file__).resolve().parent.parent / "contract"
_REQUEST_SCHEMA = _CONTRACT_DIR / "schema" / "request.schema.json"


# --- helpers --------------------------------------------------------------

def _progress(message: str) -> None:
    """Forward engine progress to stderr; stdout is reserved for the response."""
    end = "" if message.startswith("\r") else "\n"
    print(message, file=sys.stderr, end=end, flush=True)


def _relative(path: Path, base: Path) -> str:
    """Path relative to the engine root when possible (matches the contract)."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _safe_source_path(source: str, settings: Settings) -> Path:
    """Resolve a transcribe ``source`` and confine it to ``output_dir``.

    Sources come from an untrusted request, so this is the gate against path
    traversal: the source is resolved relative to the engine root and must land
    inside ``output_dir`` (where generated clips live). Absolute paths and
    ``../`` escapes resolve outside and are rejected.
    """
    allowed = settings.output_dir.resolve()
    candidate = (settings.base_dir / source).resolve()
    if candidate != allowed and not candidate.is_relative_to(allowed):
        raise CoffeeError(f"Source path is outside the allowed directory: {source!r}")
    return candidate


def _validate_request(request: dict) -> None:
    """Validate the request against the frozen JSON Schema (raises on mismatch)."""
    schema = json.loads(_REQUEST_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(request, schema)


def _options(request: dict) -> dict:
    return request.get("options") or {}


def _search_namespace(options: dict) -> SimpleNamespace:
    """Adapt request options to the namespace ``build_search_service`` expects."""
    return SimpleNamespace(
        semantic=bool(options.get("semantic", False)),
        model=options.get("model", "local"),
        classify=bool(options.get("classify", False)),
        top_k=options.get("top_k"),
        threshold=options.get("threshold"),
    )


# --- action handlers ------------------------------------------------------

def _fragment_payload(hit: SearchHit) -> dict:
    """Serialize a search hit to the contract's search-result shape."""
    topic = hit.topic
    return {
        "id": to_id(hit.fragment),
        "episode": episode_number(hit.episode.title),
        "date": f"{hit.episode.date:%Y-%m-%d}",
        "start": topic.start,
        "end": topic.end,
        "duration": topic.duration,
        "name": topic.name,
        # Real ranking metadata: cosine score (semantic) and the LLM reason
        # (when --classify ran). Both are null for keyword search.
        "score": hit.score,
        "reason": hit.reason,
    }


def _do_search(request: dict, settings: Settings) -> dict:
    options = _options(request)
    search_service = build_search_service(settings, _search_namespace(options))
    service, _cache = build_service(settings, search_service)

    episodes = service.load_episodes()
    hits = service.search(episodes, request.get("query", ""))
    limit = options.get("limit")
    if limit:
        hits = hits[:limit]

    return {
        "version": CONTRACT_VERSION,
        "action": "search",
        "ok": True,
        "fragments": [_fragment_payload(hit) for hit in hits],
    }


def _do_generate(request: dict, settings: Settings) -> dict:
    options = _options(request)
    search_service = build_search_service(settings, _search_namespace(options))
    service, _cache = build_service(settings, search_service)

    episodes = service.load_episodes()
    fragments = resolve(episodes, request.get("selection") or [])
    if not fragments:
        raise CoffeeError("No fragments resolved from the selection.")

    query = request.get("query", "clip")
    out_path = settings.output_dir / f"{slugify(query)}_{datetime.now():%Y-%m-%d}.mp3"
    split = options.get("split")
    outputs = service.build_clips(
        fragments,
        out_path,
        keep_temp=False,
        intro=options.get("intro", True),
        disclaimer=options.get("disclaimer", True),
        split_seconds=split * 60 if split else None,
        report=_progress,
    )

    ffmpeg = FFmpeg(settings)
    artifacts = []
    for path in outputs:
        artifacts.append({
            "path": _relative(path, settings.base_dir),
            "duration": round(ffmpeg.probe_duration(path)),
            "size_bytes": path.stat().st_size,
        })
    return {
        "version": CONTRACT_VERSION,
        "action": "generate",
        "ok": True,
        "artifacts": artifacts,
    }


def _do_transcribe(request: dict, settings: Settings) -> dict:
    transcriber = FasterWhisperTranscriber()
    transcripts = []
    for source in request.get("selection") or []:
        path = _safe_source_path(source, settings)  # path-traversal guard
        written = transcriber.transcribe(path)
        transcripts.append({
            "source": _relative(path, settings.base_dir),
            "txt": _relative(written["txt"], settings.base_dir),
            "srt": _relative(written["srt"], settings.base_dir),
        })
    return {
        "version": CONTRACT_VERSION,
        "action": "transcribe",
        "ok": True,
        "transcripts": transcripts,
    }


def _chat_payload(answer: RagAnswer) -> dict:
    """Serialize a grounded answer to the contract's chat shape.

    Several retrieved passages may come from the same fragment; they collapse to
    one citation (keyed by fragment id) so ``sources`` lists each episode once.
    """
    seen: set[str] = set()
    sources = []
    for passage in answer.sources:
        if passage.fragment_id in seen:
            continue
        seen.add(passage.fragment_id)
        sources.append({
            "episode": passage.episode,
            "date": passage.date,
            "topic": passage.topic,
        })
    return {
        "version": CONTRACT_VERSION,
        "action": "chat",
        "ok": True,
        "answer": answer.text,
        "sources": sources,
    }


def _do_chat(request: dict, settings: Settings) -> dict:
    question = request.get("query", "").strip()
    if not question:
        raise CoffeeError("A 'query' (the question to ask) is required for chat.")

    options = _options(request)
    search_service = build_search_service(settings, _search_namespace(options))
    service, _cache = build_service(settings, search_service)

    episodes = service.load_episodes()
    fragments = resolve(episodes, request.get("selection") or [])
    if not fragments:
        raise CoffeeError("No fragments resolved from the selection.")

    rag = build_rag_service(settings, model=options.get("model", "local"))
    answerer = rag.open_session(fragments)
    return _chat_payload(answerer.answer(question))


def _book_payload(artifacts: list[tuple[Path, str]], settings: Settings) -> dict:
    """Serialize produced book files to the contract's book shape."""
    return {
        "version": CONTRACT_VERSION,
        "action": "book",
        "ok": True,
        "artifacts": [
            {"path": _relative(path, settings.base_dir), "format": fmt}
            for path, fmt in artifacts
        ],
    }


def _do_book(request: dict, settings: Settings) -> dict:
    options = _options(request)
    search_service = build_search_service(settings, _search_namespace(options))
    service, _cache = build_service(settings, search_service)

    episodes = service.load_episodes()
    fragments = resolve(episodes, request.get("selection") or [])
    if not fragments:
        raise CoffeeError("No fragments resolved from the selection.")

    title = request.get("query") or "Coffee Break"
    composer = build_book_composer(settings, model=options.get("model", "local"))
    book = composer.compose(fragments, title)

    md_path = settings.output_dir / f"{slugify(title)}_{datetime.now():%Y-%m-%d}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(MarkdownRenderer().render(book), encoding="utf-8")

    artifacts: list[tuple[Path, str]] = [(md_path, "markdown")]
    artifacts += PandocExporter().export(
        md_path, options.get("formats", ["pdf", "epub"]), report=_progress
    )
    return _book_payload(artifacts, settings)


_HANDLERS = {
    "search": _do_search,
    "generate": _do_generate,
    "transcribe": _do_transcribe,
    "chat": _do_chat,
    "book": _do_book,
}


# --- entry point ----------------------------------------------------------

def handle(request: dict, settings: Settings | None = None) -> dict:
    """Run one request and return the response dict (no I/O). Used by tests."""
    settings = settings or Settings.from_env()
    _validate_request(request)
    action = request["action"]

    # Defensive cap: a huge selection would trigger mass downloads/transcriptions.
    selection = request.get("selection") or []
    if len(selection) > settings.max_selection:
        raise CoffeeError(
            f"Too many items in selection: {len(selection)} "
            f"(max {settings.max_selection})."
        )

    handler = _HANDLERS.get(action)
    if handler is None:
        raise CoffeeError(f"Action '{action}' is not implemented yet.")
    return handler(request, settings)


def _error_response(action: str | None, message: str, code: int) -> dict:
    response = {"version": CONTRACT_VERSION, "ok": False, "error": message, "code": code}
    if action:
        response["action"] = action
    return response


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.read()
    action = None
    try:
        request = json.loads(raw)
        action = request.get("action") if isinstance(request, dict) else None
        response = handle(request)
        print(json.dumps(response, ensure_ascii=False))
        return 0
    except json.JSONDecodeError as error:
        print(json.dumps(_error_response(None, f"Invalid JSON: {error}", 1)))
        return 1
    except CoffeeError as error:
        print(json.dumps(_error_response(action, str(error), 1), ensure_ascii=False))
        return 1
    except jsonschema.ValidationError as error:
        # Schema messages are safe and helpful for the caller.
        text = f"Invalid request: {error.message}"
        print(json.dumps(_error_response(action, text, 1), ensure_ascii=False))
        return 1
    except KeyboardInterrupt:
        print(json.dumps(_error_response(action, "Interrupted.", 130)))
        return 130
    except Exception as error:  # anything unexpected: log details, do not leak them
        print(f"engine: unexpected error: {error!r}", file=sys.stderr)
        print(json.dumps(_error_response(action, "Unexpected engine error.", 1)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
