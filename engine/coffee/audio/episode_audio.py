"""Resolve an episode to its local audio file (Adapter over cache + downloader).

A small collaborator that turns an ``Episode`` into a path to its full MP3,
downloading it once and reusing the cached copy on later calls. It exists so the
RAG read side can obtain fragment audio without depending on the whole
``ClipAssembler``; the heavy episode download stays a single, shared concern.
"""

from __future__ import annotations

from pathlib import Path

from coffee.audio.downloader import AudioDownloader
from coffee.config import Settings
from coffee.domain.models import Episode
from coffee.infrastructure.json_cache import JsonCache


class EpisodeAudioProvider:
    """Returns the local MP3 path for an episode, downloading on a cache miss."""

    def __init__(
        self, settings: Settings, cache: JsonCache, downloader: AudioDownloader
    ) -> None:
        self._settings = settings
        self._cache = cache
        self._downloader = downloader

    def __call__(self, episode: Episode) -> Path:
        dest = self._cache.episode_audio_path(episode.guid)
        if self._cache.is_episode_downloaded(episode.guid):
            return dest
        self._settings.episodes_dir.mkdir(parents=True, exist_ok=True)
        self._downloader.download(episode.audio_url, dest)
        return dest
