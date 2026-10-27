"""Search service.

A thin service that delegates to an injected ``SearchStrategy``. It is the stable
entry point used by the orchestrator, so swapping strategies (keyword today,
semantic tomorrow) never ripples outward.
"""

from __future__ import annotations

from coffee.domain.models import Episode, SearchHit
from coffee.search.search_strategy import SearchStrategy


class SearchService:
    """Runs a search using the injected strategy (Strategy pattern client)."""

    def __init__(self, strategy: SearchStrategy) -> None:
        self._strategy = strategy

    def search(self, episodes: list[Episode], query: str) -> list[SearchHit]:
        return self._strategy.search(episodes, query)
