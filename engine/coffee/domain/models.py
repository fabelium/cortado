"""Domain value objects.

These are pure, immutable data structures (frozen dataclasses) with no
knowledge of networking, disk or external services. They model the problem
domain: a podcast made of ``Episode``s, each containing ``Topic``s anchored to
a ``TimeRange``, and a ``Fragment`` which pairs a search hit (episode + topic).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeRange:
    """A half-open time window ``[start, end)`` in whole seconds.

    ``end`` is ``None`` for the last topic of an episode, whose end is unknown
    (it runs until the audio finishes).
    """

    start: int           # absolute seconds from the start of the episode
    end: int | None      # start of the next topic; None means "until the end"

    @property
    def duration(self) -> int | None:
        """Length in seconds, or ``None`` when the end is unknown."""
        if self.end is None:
            return None
        return max(0, self.end - self.start)


@dataclass(frozen=True)
class Topic:
    """A subject discussed inside an episode, pinned to a time window."""

    name: str             # e.g. "How supermassive black holes feed"
    time_range: TimeRange

    @property
    def start(self) -> int:
        return self.time_range.start

    @property
    def end(self) -> int | None:
        return self.time_range.end

    @property
    def duration(self) -> int | None:
        return self.time_range.duration


@dataclass(frozen=True)
class Episode:
    """A podcast episode with its already-resolved topics."""

    guid: str                  # stable identifier (used for cache and downloads)
    title: str                 # e.g. "Ep563_B: Antihydrogen; Bone marrow..."
    date: datetime             # publication date, for chronological ordering
    audio_url: str             # URL of the MP3 enclosure
    topics: tuple[Topic, ...]  # immutable so Episode stays hashable/frozen


@dataclass(frozen=True)
class Fragment:
    """A matched piece of audio: an episode together with one of its topics."""

    episode: Episode
    topic: Topic

    @property
    def date(self) -> datetime:
        return self.episode.date


@dataclass(frozen=True)
class SearchHit:
    """A search result: a ``Fragment`` plus optional ranking metadata.

    Keeping ranking data here (instead of on ``Fragment``) separates the domain
    entity from query-specific information. ``score`` is the semantic similarity
    (``None`` for keyword search); ``reason`` is the LLM relevance justification
    (``None`` unless classification ran). The fragment's own fields are exposed
    as pass-through properties for convenience.
    """

    fragment: Fragment
    score: float | None = None
    reason: str | None = None

    @property
    def episode(self) -> Episode:
        return self.fragment.episode

    @property
    def topic(self) -> Topic:
        return self.fragment.topic

    @property
    def date(self) -> datetime:
        return self.fragment.date
