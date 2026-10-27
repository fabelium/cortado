"""Semantic search & relevance classifier tests with fake AI providers.

No model download and no network: a deterministic fake embedding provider and a
fake chat model exercise ranking, threshold/top-k, the on-disk vector cache and
the LLM filter. Run: python3 tests/test_semantic_search.py
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.ai.relevance_classifier import RelevanceClassifier
from coffee.config import Settings
from coffee.domain.models import Episode, TimeRange, Topic
from coffee.infrastructure.embedding_cache import EmbeddingCache
from coffee.search.semantic_search_strategy import SemanticSearchStrategy


class FakeEmbeddings:
    """Maps known words to fixed vectors; everything else is orthogonal.

    'galaxy'/'galaxia' share a direction, 'recipe'/'receta' another, so cosine
    similarity is fully predictable. Tracks how many documents it embedded to
    prove the cache avoids recomputation.
    """

    _VECTORS = {
        "galaxia": [1.0, 0.0, 0.0],
        "galaxy": [1.0, 0.0, 0.0],
        "galaxias": [0.95, 0.0, 0.0],
        "receta": [0.0, 1.0, 0.0],
    }

    def __init__(self):
        self.embedded_documents = 0

    @property
    def model_id(self):
        return "fake-model"

    def _vector(self, text):
        for word, vector in self._VECTORS.items():
            if word in text.lower():
                return vector
        return [0.0, 0.0, 1.0]  # orthogonal "unknown" direction

    def embed_documents(self, texts):
        self.embedded_documents += len(texts)
        return [self._vector(t) for t in texts]

    def embed_query(self, text):
        return self._vector(text)


class FakeChat:
    """Returns a scripted JSON verdict list; records the prompt it received."""

    def __init__(self, response):
        self._response = response
        self.model_id = "fake-chat"
        self.last_prompt = None

    def complete(self, prompt, *, system=None):
        self.last_prompt = prompt
        return self._response


def _episode(name, start=0):
    topic = Topic(name=name, time_range=TimeRange(start=start, end=start + 60))
    return Episode("guid-" + name, "Ep1: " + name, datetime(2020, 1, 1), "url", (topic,))


def _settings():
    tmp = Path(tempfile.mkdtemp())
    return Settings(cache_dir=tmp, episodes_dir=tmp / "ep", feed_cache_file=tmp / "f.json")


def test_ranks_by_similarity_and_threshold():
    episodes = [_episode("Una galaxia lejana"), _episode("Una receta de cocina")]
    settings = _settings()
    fake = FakeEmbeddings()
    strategy = SemanticSearchStrategy(
        fake, EmbeddingCache(settings, fake.model_id), threshold=0.5
    )
    results = strategy.search(episodes, "galaxy")
    # Only the galaxy topic is above threshold; the recipe is orthogonal.
    assert len(results) == 1
    assert "galaxia" in results[0].topic.name.lower()


def test_vector_cache_avoids_recomputation():
    episodes = [_episode("Una galaxia"), _episode("Otra galaxias")]
    settings = _settings()
    fake = FakeEmbeddings()
    cache = EmbeddingCache(settings, fake.model_id)

    SemanticSearchStrategy(fake, cache, threshold=0.1).search(episodes, "galaxy")
    first = fake.embedded_documents
    assert first == 2  # both topics embedded once

    # A fresh strategy + fresh provider reuses the persisted vectors.
    fake2 = FakeEmbeddings()
    SemanticSearchStrategy(fake2, EmbeddingCache(settings, fake.model_id),
                           threshold=0.1).search(episodes, "galaxy")
    assert fake2.embedded_documents == 0  # nothing re-embedded


def test_hit_exposes_cosine_score():
    episodes = [_episode("Una galaxia lejana")]
    settings = _settings()
    fake = FakeEmbeddings()
    strategy = SemanticSearchStrategy(
        fake, EmbeddingCache(settings, fake.model_id), threshold=0.1
    )
    hits = strategy.search(episodes, "galaxy")
    assert hits[0].score is not None and hits[0].score > 0.9  # surfaced score


def test_classifier_reason_attached_to_hit():
    episodes = [_episode("Una galaxia")]
    settings = _settings()
    fake = FakeEmbeddings()
    chat = FakeChat('[{"i":0,"keep":true,"reason":"trata de galaxias"}]')
    strategy = SemanticSearchStrategy(
        fake, EmbeddingCache(settings, fake.model_id), threshold=0.1,
        classifier=RelevanceClassifier(chat),
    )
    hits = strategy.search(episodes, "galaxy")
    assert hits[0].reason == "trata de galaxias"   # surfaced reason
    assert hits[0].score is not None               # score kept after classifying


def test_classifier_drops_rejected_and_parses_json():
    chat = FakeChat('[{"i":0,"keep":true,"reason":"sí"},'
                    ' {"i":1,"keep":false,"reason":"no"}]')
    verdicts = RelevanceClassifier(chat).classify("galaxy", ["Galaxia", "Receta"])
    assert [v.keep for v in verdicts] == [True, False]
    assert verdicts[1].reason == "no"


def test_classifier_degrades_to_keep_all_on_garbage():
    chat = FakeChat("not json at all")
    verdicts = RelevanceClassifier(chat).classify("x", ["A", "B"])
    assert all(v.keep for v in verdicts)  # unparseable -> keep everything


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
