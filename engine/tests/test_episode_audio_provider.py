"""EpisodeAudioProvider: resolve an episode to a local MP3, downloading it once
and reusing the cached file afterwards. Fakes for cache/downloader keep the test
free of network and disk-heavy work. Run: python3 tests/test_episode_audio_provider.py
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.audio.episode_audio import EpisodeAudioProvider
from coffee.config import Settings
from coffee.domain.models import Episode


def _episode(guid="guid237", url="http://audio/ep237.mp3"):
    return Episode(guid, "Ep237: x", datetime(2019, 10, 17), url, ())


class _FakeCache:
    def __init__(self, downloaded, path):
        self._downloaded = downloaded
        self._path = Path(path)

    def episode_audio_path(self, guid):
        return self._path

    def is_episode_downloaded(self, guid):
        return self._downloaded


class _FakeDownloader:
    def __init__(self):
        self.calls = []

    def download(self, url, dest, *, progress=None):
        self.calls.append((url, Path(dest)))
        Path(dest).write_bytes(b"audio")


def _settings():
    return Settings(episodes_dir=Path(tempfile.mkdtemp()) / "episodes")


def test_returns_cached_path_without_downloading():
    dest = Path(tempfile.mkdtemp()) / "ep.mp3"
    downloader = _FakeDownloader()
    provider = EpisodeAudioProvider(_settings(), _FakeCache(True, dest), downloader)

    result = provider(_episode())

    assert result == dest
    assert downloader.calls == []  # already cached -> no download


def test_downloads_when_missing_then_returns_path():
    dest = Path(tempfile.mkdtemp()) / "ep.mp3"
    downloader = _FakeDownloader()
    provider = EpisodeAudioProvider(_settings(), _FakeCache(False, dest), downloader)

    result = provider(_episode(url="http://audio/ep237.mp3"))

    assert result == dest
    assert downloader.calls == [("http://audio/ep237.mp3", dest)]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
