"""Split a fragment transcript into overlapping passages.

Word-based sliding window with overlap: simple, deterministic and language-
agnostic, which is enough for retrieval. The overlap keeps a sentence that
straddles a boundary recoverable from at least one passage. Each passage inherits
the fragment's citation metadata.
"""

from __future__ import annotations

from coffee.application.fragment_ref import to_id
from coffee.domain.models import Fragment
from coffee.knowledge.passage import Passage
from coffee.speech.announcements import episode_number


class PassageChunker:
    """Chunks a transcript into ``Passage``s using a sliding word window."""

    def __init__(self, target_words: int = 120, overlap_words: int = 20) -> None:
        self._target = target_words
        self._overlap = overlap_words
        # Advance by this many words per window; never below 1.
        self._step = max(1, target_words - overlap_words)

    def chunk(self, fragment: Fragment, transcript: str) -> list[Passage]:
        words = transcript.split()
        if not words:
            return []

        fragment_id = to_id(fragment)
        episode = episode_number(fragment.episode.title)
        date = f"{fragment.episode.date:%Y-%m-%d}"
        topic = fragment.topic.name

        passages: list[Passage] = []
        index = 0
        for start in range(0, len(words), self._step):
            window = words[start:start + self._target]
            passages.append(Passage(
                text=" ".join(window),
                fragment_id=fragment_id,
                episode=episode,
                date=date,
                topic=topic,
                index=index,
            ))
            index += 1
            # Stop once a window has reached the end, so the final chunk isn't
            # followed by a redundant overlap-only tail.
            if start + self._target >= len(words):
                break
        return passages
