"""Episode repository.

``EpisodeRepository`` implements the Repository pattern: it hides where episodes
come from (cache vs. live feed) behind a single ``get_episodes`` call. It serves
the cached feed when fresh, and refreshes from the ``FeedSource`` when the cache
is stale or a refresh is forced, persisting the result back to the cache.
"""

from __future__ import annotations

from coffee.domain.models import Episode
from coffee.feed.feed_source import FeedSource
from coffee.infrastructure.json_cache import JsonCache


class EpisodeRepository:
    """Repository pattern over the feed source and the JSON cache."""

    def __init__(self, feed_source: FeedSource, cache: JsonCache) -> None:
        self._feed_source = feed_source
        self._cache = cache

    def get_episodes(self, *, force_refresh: bool = False) -> list[Episode]:
        """Return episodes, using the cache when valid.

        ``force_refresh=True`` ignores the cache and re-downloads the feed.
        """
        if not force_refresh:
            cached = self._cache.load_feed()
            if cached is not None:
                return cached

        episodes = self._feed_source.fetch()
        self._cache.save_feed(episodes)
        return episodes
