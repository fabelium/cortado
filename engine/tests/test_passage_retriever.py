"""PassageRetriever: embed passages once, then return the top-k most relevant
for a query (cosine similarity). Written test-first with a deterministic fake
embedding provider (no model). Run: python3 tests/test_passage_retriever.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.knowledge.passage import Passage
from coffee.knowledge.passage_retriever import PassageRetriever


class FakeEmbeddings:
    """Maps known words to fixed directions; anything else is orthogonal."""

    _VECTORS = {
        "galaxia": [1.0, 0.0, 0.0],
        "galaxy": [1.0, 0.0, 0.0],
        "receta": [0.0, 1.0, 0.0],
        "cocina": [0.0, 1.0, 0.0],
    }

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


def _passage(text, index=0):
    return Passage(text=text, fragment_id="ep1@0-60", episode=1,
                   date="2020-01-01", topic="t", index=index)


def test_retrieves_most_relevant_first():
    retriever = PassageRetriever(FakeEmbeddings())
    retriever.index([
        _passage("una receta de cocina", 0),
        _passage("una galaxia lejana", 1),
    ])
    results = retriever.retrieve("galaxy", k=1)
    assert len(results) == 1
    assert "galaxia" in results[0].text


def test_respects_k():
    retriever = PassageRetriever(FakeEmbeddings())
    retriever.index([_passage(f"galaxia {i}", i) for i in range(3)])
    assert len(retriever.retrieve("galaxy", k=2)) == 2


def test_empty_index_returns_nothing():
    retriever = PassageRetriever(FakeEmbeddings())
    assert retriever.retrieve("galaxy", k=5) == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
