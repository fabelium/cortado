"""JSON-backed local cache.

Two cooperating caches live behind ``JsonCache``:

1. The parsed feed (list of episodes) in a single JSON file, stamped with a
   fetch time so it can be invalidated by age.
2. The full episode MP3s under ``cache/episodes/``, reusable across searches and
   named by a stable hash of the GUID.

Writes are atomic (write to ``.tmp`` then rename) and a corrupt cache is treated
as absent, so the caller simply regenerates it instead of crashing.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from coffee.config import Settings
from coffee.domain.models import Episode, TimeRange, Topic


class JsonCache:
    """Feed cache (age-invalidated) plus episode-audio cache (hashed paths)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # --- Episode (de)serialization -----------------------------------------

    @staticmethod
    def _episode_to_dict(episode: Episode) -> dict:
        return {
            "guid": episode.guid,
            "title": episode.title,
            "date": episode.date.isoformat(),
            "audio_url": episode.audio_url,
            "topics": [
                {"name": t.name, "start": t.start, "end": t.end}
                for t in episode.topics
            ],
        }

    @staticmethod
    def _episode_from_dict(data: dict) -> Episode:
        return Episode(
            guid=data["guid"],
            title=data["title"],
            date=datetime.fromisoformat(data["date"]),
            audio_url=data["audio_url"],
            topics=tuple(
                Topic(name=t["name"], time_range=TimeRange(start=t["start"], end=t["end"]))
                for t in data["topics"]
            ),
        )

    # --- Feed cache ---------------------------------------------------------

    def save_feed(self, episodes: list[Episode]) -> None:
        """Persist the parsed feed atomically (write to .tmp, then rename)."""
        self._settings.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(episodes),
            "episodes": [self._episode_to_dict(e) for e in episodes],
        }
        path = self._settings.feed_cache_file
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    def load_feed(self) -> list[Episode] | None:
        """Return the cached episodes, or ``None`` if missing or expired.

        A corrupt cache is treated as absent (returns ``None``) so the flow can
        regenerate it without breaking.
        """
        path = self._settings.feed_cache_file
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(payload["fetched_at"])
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            return None

        age_seconds = (datetime.now(timezone.utc) - fetched_at).total_seconds()
        if age_seconds > self._settings.feed_max_age_hours * 3600:
            return None
        try:
            return [self._episode_from_dict(d) for d in payload["episodes"]]
        except (KeyError, ValueError):
            return None

    # --- Episode-audio cache ------------------------------------------------

    def episode_audio_path(self, guid: str) -> Path:
        """Stable path of an episode's full MP3, derived from its GUID."""
        digest = hashlib.sha1(guid.encode("utf-8")).hexdigest()[:16]
        return self._settings.episodes_dir / f"{digest}.mp3"

    def is_episode_downloaded(self, guid: str) -> bool:
        """True if the episode MP3 is already cached and non-empty."""
        path = self.episode_audio_path(guid)
        return path.exists() and path.stat().st_size > 0

    # --- Maintenance --------------------------------------------------------

    def clear(self) -> tuple[int, int]:
        """Delete the whole cache (feed + episodes). Returns (file count, bytes)."""
        files = 0
        size = 0
        cache_dir = self._settings.cache_dir
        if cache_dir.exists():
            for path in cache_dir.rglob("*"):
                if path.is_file():
                    files += 1
                    size += path.stat().st_size
            shutil.rmtree(cache_dir)
        return files, size
