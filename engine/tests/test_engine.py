"""Tests for the JSON entry point (engine.py) against the frozen contract.

Pure checks (id round-trip, request validation, reserved actions) run offline.
One integration check exercises a real keyword `search` over the cached feed and
validates the response against the actual contract schema, proving the engine
emits exactly what the API expects. Run: python3 tests/test_engine.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jsonschema

import engine
from coffee.application.fragment_ref import resolve, to_id
from coffee.domain.errors import CoffeeError, NetworkError
from coffee.domain.models import Episode, TimeRange, Topic

_CONTRACT = Path(__file__).resolve().parent.parent.parent / "contract"


def _schema(name):
    return json.loads((_CONTRACT / "schema" / name).read_text(encoding="utf-8"))


def _episode(number, name, start, end):
    topic = Topic(name=name, time_range=TimeRange(start=start, end=end))
    return Episode(f"guid{number}", f"Ep{number}: x", datetime(2019, 10, 17),
                   "http://audio", (topic,))


def test_fragment_id_roundtrip():
    from coffee.domain.models import Fragment

    episodes = [_episode(237, "Insight en Marte", 300, 480),
                _episode(563, "Agujeros negros", 0, 2140)]
    ids = [to_id(Fragment(episode=e, topic=e.topics[0])) for e in episodes]
    assert ids[0] == "ep237@300-480"
    resolved = resolve(episodes, ids)
    assert [to_id(f) for f in resolved] == ids  # exact round-trip


def test_open_ended_id():
    from coffee.domain.models import Fragment
    e = _episode(563, "Señales de los oyentes", 5910, None)
    assert to_id(Fragment(episode=e, topic=e.topics[0])) == "ep563@5910-"


def test_unknown_action_is_rejected_by_schema():
    """Actions outside the contract enum are rejected at schema validation."""
    try:
        engine.handle({"version": "1.0", "action": "unknown_action"})
    except jsonschema.ValidationError:
        pass  # expected: schema rejects actions outside the enum
    else:
        raise AssertionError("unknown action must fail schema validation")


def test_bad_version_is_rejected():
    try:
        engine.handle({"version": "0.9", "action": "search"})
    except Exception as error:
        assert isinstance(error, jsonschema.ValidationError)
    else:
        raise AssertionError("a wrong version must fail validation")


def test_error_response_shape():
    response = engine._error_response("search", "boom", 1)
    jsonschema.validate(response, _schema("response.error.schema.json"))


def test_search_response_matches_schema():
    """Integration: real keyword search over the cached feed (skips if offline)."""
    request = {"version": "1.0", "action": "search", "query": "marte",
               "options": {"limit": 5}}
    try:
        response = engine.handle(request)
    except NetworkError:
        print("  (skipped: no cache and no network)")
        return
    jsonschema.validate(response, _schema("response.search.schema.json"))
    assert response["ok"] is True
    assert len(response["fragments"]) >= 1
    assert all(f["id"].startswith("ep") and "@" in f["id"]
               for f in response["fragments"])


def test_chat_payload_matches_schema_and_dedupes_sources():
    """A grounded answer serializes to the chat contract; repeated fragments
    collapse to one source (passages from the same fragment cite once)."""
    from coffee.knowledge.passage import Passage
    from coffee.knowledge.rag_answerer import RagAnswer

    passages = [
        Passage("la sonda Insight aterrizó en Marte", "ep237@300-480",
                237, "2019-10-17", "Insight en Marte", 0),
        Passage("detalles del aterrizaje", "ep237@300-480",
                237, "2019-10-17", "Insight en Marte", 1),
    ]
    answer = RagAnswer("Insight aterrizó en Marte en 2018 (237).", passages)

    payload = engine._chat_payload(answer)

    jsonschema.validate(payload, _schema("response.chat.schema.json"))
    assert payload["answer"].endswith("(237).")
    assert payload["sources"] == [
        {"episode": 237, "date": "2019-10-17", "topic": "Insight en Marte"}
    ]


def test_chat_payload_without_sources_keeps_guardrail_answer():
    """The 'I don't know' answer (no passages) is a valid, source-less response."""
    from coffee.knowledge.rag_answerer import RagAnswer

    answer = RagAnswer("No encuentro información sobre eso.", [])

    payload = engine._chat_payload(answer)

    jsonschema.validate(payload, _schema("response.chat.schema.json"))
    assert payload["sources"] == []


def test_book_payload_matches_schema_with_relative_paths():
    """Artifacts serialize to the book contract with engine-relative paths."""
    from coffee.config import Settings

    settings = Settings()
    base = settings.base_dir
    artifacts = [
        (base / "output" / "marte.md", "markdown"),
        (base / "output" / "marte.pdf", "pdf"),
    ]

    payload = engine._book_payload(artifacts, settings)

    jsonschema.validate(payload, _schema("response.book.schema.json"))
    assert payload["artifacts"][0] == {"path": "output/marte.md", "format": "markdown"}
    assert payload["artifacts"][1]["format"] == "pdf"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
