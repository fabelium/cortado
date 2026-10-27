"""Semantic search strategy (Strategy adapter, embeddings + optional LLM filter).

Implements the same ``SearchStrategy`` port as the keyword adapter, so it drops
into the existing ``SearchService`` with no caller changes. It embeds every topic
name once (cached on disk), embeds the query, ranks topics by cosine similarity,
keeps those above a threshold (top-k), and can optionally pass the survivors
through an LLM ``RelevanceClassifier`` for a final include/exclude judgement.

Results are returned ranked by relevance (best first) for display. The audio is
made chronological later, in the assembler, which is the single owner of the
"chronological output" promise.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from coffee.ai.embedding_provider import EmbeddingProvider
from coffee.ai.relevance_classifier import RelevanceClassifier
from coffee.domain.models import Episode, Fragment, SearchHit
from coffee.infrastructure.embedding_cache import EmbeddingCache
from coffee.search.search_strategy import SearchStrategy

Reporter = Callable[[str], None]


class SemanticSearchStrategy(SearchStrategy):
    """Adapter: ranks fragments by embedding similarity to the query."""

    def __init__(
        self,
        embeddings: EmbeddingProvider,
        cache: EmbeddingCache,
        *,
        top_k: int = 30,
        threshold: float = 0.30,
        classifier: RelevanceClassifier | None = None,
        report: Reporter = lambda _msg: None,
    ) -> None:
        self._embeddings = embeddings
        self._cache = cache
        self._top_k = top_k
        self._threshold = threshold
        self._classifier = classifier
        self._report = report

    @staticmethod
    def _key(fragment: Fragment) -> str:
        """Stable cache key for a topic (survives reordering, not renaming)."""
        topic = fragment.topic
        return f"{fragment.episode.guid}:{topic.start}:{topic.name}"

    def _all_fragments(self, episodes: list[Episode]) -> list[Fragment]:
        return [
            Fragment(episode=episode, topic=topic)
            for episode in episodes
            for topic in episode.topics
        ]

    def _vectors_for(self, fragments: list[Fragment]) -> np.ndarray:
        """Return the (n, d) matrix of topic vectors, embedding only cache misses."""
        cached = self._cache.load()
        missing = [f for f in fragments if self._key(f) not in cached]
        if missing:
            self._report(
                f"  embedding {len(missing)} new topic(s) "
                f"(reusing {len(fragments) - len(missing)} cached)..."
            )
            new_vectors = self._embeddings.embed_documents(
                [f.topic.name for f in missing]
            )
            for fragment, vector in zip(missing, new_vectors):
                cached[self._key(fragment)] = np.asarray(vector, dtype=np.float32)
            self._cache.save(cached)
        return np.array([cached[self._key(f)] for f in fragments], dtype=np.float32)

    @staticmethod
    def _cosine_scores(matrix: np.ndarray, query: np.ndarray) -> np.ndarray:
        """Cosine similarity of every row in ``matrix`` against ``query``."""
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)
        query_norm = query / (np.linalg.norm(query) + 1e-12)
        return matrix_norm @ query_norm

    def search(self, episodes: list[Episode], query: str) -> list[SearchHit]:
        fragments = self._all_fragments(episodes)
        if not fragments or not query.strip():
            return []

        matrix = self._vectors_for(fragments)
        query_vector = np.asarray(self._embeddings.embed_query(query), dtype=np.float32)
        scores = self._cosine_scores(matrix, query_vector)

        # Rank by similarity, keep those above the threshold, cap at top_k. The
        # rounded cosine similarity becomes the hit's score.
        order = np.argsort(scores)[::-1]
        ranked = [
            SearchHit(fragments[i], score=round(float(scores[i]), 4))
            for i in order
            if scores[i] >= self._threshold
        ][: self._top_k]

        if self._classifier and ranked:
            ranked = self._apply_classifier(query, ranked)
        return ranked

    def _apply_classifier(self, query: str, ranked: list[SearchHit]) -> list[SearchHit]:
        """Drop hits the LLM judges off-topic, attaching its reason to the rest."""
        self._report(f"  classifying {len(ranked)} candidate(s) with the LLM...")
        verdicts = self._classifier.classify(query, [h.topic.name for h in ranked])
        kept: list[SearchHit] = []
        for hit, verdict in zip(ranked, verdicts):
            mark = "+" if verdict.keep else "-"
            self._report(f"    {mark} {hit.topic.name[:55]} — {verdict.reason}")
            if verdict.keep:
                kept.append(SearchHit(hit.fragment, score=hit.score, reason=verdict.reason))
        return kept
