"""Per-fragment transcript store (cache-aside pattern).

Transcribing a topic's audio segment is expensive (whisper) but the segment
never changes, so each fragment is transcribed at most once and its text is
persisted, keyed by the fragment id (episode + time range). The actual
transcription work is injected as a ``producer`` callable, keeping this class
free of audio/whisper concerns and trivial to test.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from coffee.application.fragment_ref import to_id
from coffee.domain.models import Fragment

# A producer turns a fragment into its transcript text (cut segment + transcribe).
TranscriptProducer = Callable[[Fragment], str]


class TranscriptStore:
    """Returns a fragment's transcript, producing and caching it on a miss."""

    def __init__(self, path: Path, producer: TranscriptProducer) -> None:
        self._path = Path(path)
        self._producer = producer

    def get(self, fragment: Fragment) -> str:
        """Return the transcript for ``fragment`` (from cache, or produce it)."""
        key = to_id(fragment)
        cache = self._load()
        if key in cache:
            return cache[key]
        text = self._producer(fragment)
        cache[key] = text
        self._save(cache)
        return text

    # --- persistence --------------------------------------------------------

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}  # a corrupt cache is treated as empty and rebuilt

    def _save(self, cache: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)
