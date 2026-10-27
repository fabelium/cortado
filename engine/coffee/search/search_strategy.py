"""Search strategy port and its keyword adapter (Strategy pattern).

``SearchStrategy`` is the port: a single ``search`` method that maps a query +
episodes to ranked ``SearchHit``s. ``KeywordSearchStrategy`` is the current
adapter (accent-insensitive AND matching). The seam is deliberately open: the
``SemanticSearchStrategy`` (embeddings + LLM relevance) implements the same port.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from coffee.domain.models import Episode, Fragment, SearchHit
from coffee.search.text import normalize


class SearchStrategy(ABC):
    """Port: a strategy that finds hits matching a query."""

    @abstractmethod
    def search(self, episodes: list[Episode], query: str) -> list[SearchHit]:
        """Return the hits matching ``query`` (ranking order set by the strategy)."""
        raise NotImplementedError


class KeywordSearchStrategy(SearchStrategy):
    """Adapter: accent-insensitive, case-insensitive, AND keyword matching.

    A topic matches when its name contains ALL the words in the query. Keyword
    search has no relevance score, so hits carry ``score=None``.
    """

    def search(self, episodes: list[Episode], query: str) -> list[SearchHit]:
        words = [word for word in normalize(query).split() if word]
        if not words:
            return []

        results: list[SearchHit] = []
        for episode in episodes:
            for topic in episode.topics:
                haystack = normalize(topic.name)
                if all(word in haystack for word in words):
                    results.append(SearchHit(Fragment(episode=episode, topic=topic)))

        # Chronological order, oldest first.
        results.sort(key=lambda hit: hit.date)
        return results
