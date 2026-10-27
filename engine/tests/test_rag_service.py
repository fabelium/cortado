"""RagService: wire transcript store + chunker + retriever + answerer into a
chat session over a set of fragments. Written test-first with fakes (no whisper,
no embeddings model, no API). Run: python3 tests/test_rag_service.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.application.fragment_ref import to_id
from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.knowledge.chunker import PassageChunker
from coffee.knowledge.rag_service import RagService


class FakeEmbeddings:
    _VECTORS = {"galaxia": [1.0, 0.0, 0.0], "galaxy": [1.0, 0.0, 0.0]}

    @property
    def model_id(self):
        return "fake"

    def _vector(self, text):
        for word, vector in self._VECTORS.items():
            if word in text.lower():
                return vector
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts):
        return [self._vector(t) for t in texts]

    def embed_query(self, text):
        return self._vector(text)


class FakeChat:
    def __init__(self, response="una respuesta"):
        self._response = response
        self.model_id = "fake"

    def complete(self, prompt, *, system=None):
        return self._response


class FakeStore:
    """Returns a fixed transcript for any fragment; records the calls."""

    def __init__(self, text):
        self._text = text
        self.gets = []

    def get(self, fragment):
        self.gets.append(fragment)
        return self._text


def _fragment(number=237, start=0, end=60):
    topic = Topic(name="t", time_range=TimeRange(start=start, end=end))
    episode = Episode(f"guid{number}", f"Ep{number}: x", datetime(2020, 1, 1),
                      "http://audio", (topic,))
    return Fragment(episode=episode, topic=topic)


def _service(store, chat=None):
    return RagService(store, PassageChunker(target_words=50, overlap_words=10),
                      FakeEmbeddings(), chat or FakeChat())


def test_session_answers_grounded_in_fragment_transcripts():
    fragment = _fragment(237)
    store = FakeStore("una galaxia lejana y muy brillante")
    answerer = _service(store, FakeChat(response="respuesta")).open_session([fragment])
    result = answerer.answer("galaxy")
    assert result.sources
    assert result.sources[0].fragment_id == to_id(fragment)
    assert result.text == "respuesta"


def test_no_fragments_gives_dont_know():
    answerer = _service(FakeStore("")).open_session([])
    result = answerer.answer("galaxy")
    assert result.sources == []
    assert "no encuentro" in result.text.lower()


def test_transcribes_each_fragment_once():
    store = FakeStore("una galaxia")
    fragments = [_fragment(1), _fragment(2)]
    _service(store).open_session(fragments)
    assert len(store.gets) == 2  # one transcript request per fragment


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
