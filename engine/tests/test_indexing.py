"""build_passage_index: transcribe (cached) -> chunk -> index, returning a ready
PassageRetriever. Fakes keep it offline. Run: python3 tests/test_indexing.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.knowledge.indexing import build_passage_index
from coffee.knowledge.passage import Passage


def _fragment(name="Marte", start=0, end=10):
    topic = Topic(name=name, time_range=TimeRange(start=start, end=end))
    episode = Episode("g", "Ep237: x", datetime(2019, 10, 17), "u", (topic,))
    return Fragment(episode=episode, topic=topic)


class _FakeStore:
    def get(self, fragment):
        return f"transcript of {fragment.topic.name}"


class _FakeChunker:
    def chunk(self, fragment, transcript):
        return [Passage(transcript, "ep237@0-10", 237, "2019-10-17",
                        fragment.topic.name, 0)]


class _FakeRetriever:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.indexed = None

    def index(self, passages):
        self.indexed = passages


def test_builds_an_index_over_chunked_transcripts(monkeypatch=None):
    import coffee.knowledge.indexing as indexing
    captured = {}

    def fake_retriever_cls(embeddings):
        r = _FakeRetriever(embeddings)
        captured["retriever"] = r
        return r

    original = indexing.PassageRetriever
    indexing.PassageRetriever = fake_retriever_cls
    try:
        retriever = build_passage_index(
            [_fragment("Marte"), _fragment("Júpiter")],
            _FakeStore(), _FakeChunker(), embeddings="EMB",
        )
    finally:
        indexing.PassageRetriever = original

    assert retriever is captured["retriever"]
    assert retriever.embeddings == "EMB"
    assert len(retriever.indexed) == 2   # one passage per fragment, indexed together


if __name__ == "__main__":
    test_builds_an_index_over_chunked_transcripts()
    print("  ok  test_builds_an_index_over_chunked_transcripts")
    print("\n1 tests OK")
