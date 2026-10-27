"""A retrievable passage: a chunk of a fragment's transcript plus its source.

Passages are the unit the future RAG layer embeds, retrieves and cites. Each one
remembers which fragment it came from (id + episode + date + topic) so an answer
can point back to the exact episode.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Passage:
    """A chunk of transcript text tagged with its source metadata."""

    text: str
    fragment_id: str   # e.g. "ep237@300-480"
    episode: int       # episode number, for citations
    date: str          # ISO date (YYYY-MM-DD) of the episode
    topic: str         # the topic/segment name
    index: int         # position of this chunk within the fragment (0-based)
