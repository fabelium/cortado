"""TranscriptStore: per-fragment transcripts are produced once and cached
forever (keyed by episode+timerange). Written test-first. A fake producer keeps
the test free of whisper and audio. Run: python3 tests/test_transcript_store.py
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.knowledge.transcript_store import TranscriptStore


def _fragment(number=237, name="Insight en Marte", start=300, end=480):
    topic = Topic(name=name, time_range=TimeRange(start=start, end=end))
    episode = Episode(f"guid{number}", f"Ep{number}: x", datetime(2019, 10, 17),
                      "http://audio", (topic,))
    return Fragment(episode=episode, topic=topic)


def _store_path():
    return Path(tempfile.mkdtemp()) / "transcripts.json"


def test_produces_once_then_serves_from_cache():
    calls = []

    def produce(fragment):
        calls.append(fragment)
        return "la sonda Insight aterrizó en Marte"

    store = TranscriptStore(_store_path(), produce)
    fragment = _fragment()
    assert store.get(fragment) == "la sonda Insight aterrizó en Marte"
    assert store.get(fragment) == "la sonda Insight aterrizó en Marte"
    assert len(calls) == 1  # produced once, then served from cache


def test_persists_across_instances():
    path = _store_path()
    TranscriptStore(path, lambda f: "primera vez").get(_fragment())

    calls = []

    def produce(fragment):
        calls.append(fragment)
        return "no debería ejecutarse"

    reused = TranscriptStore(path, produce).get(_fragment())
    assert reused == "primera vez"   # value persisted on disk
    assert calls == []               # producer never ran on a cache hit


def test_distinct_fragments_are_cached_separately():
    calls = []

    def produce(fragment):
        calls.append(fragment.topic.name)
        return f"transcript of {fragment.topic.name}"

    store = TranscriptStore(_store_path(), produce)
    a = store.get(_fragment(name="Marte", start=300, end=480))
    b = store.get(_fragment(name="Júpiter", start=900, end=1200))
    assert a != b
    assert len(calls) == 2  # two different fragments -> two productions


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
