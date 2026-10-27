"""JsonCache: feed round-trip with age invalidation (corrupt = absent), hashed
episode-audio paths and full-cache clear. Run: python3 tests/test_json_cache.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.config import Settings
from coffee.domain.models import Episode, TimeRange, Topic
from coffee.infrastructure.json_cache import JsonCache


def _settings(tmp_path, **overrides):
    return Settings(
        cache_dir=tmp_path / "cache",
        episodes_dir=tmp_path / "cache" / "episodes",
        feed_cache_file=tmp_path / "cache" / "feed_cache.json",
        output_dir=tmp_path / "output",
        **overrides,
    )


def _episodes():
    topic = Topic(name="Agujeros negros", time_range=TimeRange(start=0, end=2140))
    open_topic = Topic(name="Señales", time_range=TimeRange(start=2140, end=None))
    return [Episode("guid-1", "Ep237: x", datetime(2019, 10, 17),
                    "http://cdn/a.mp3", (topic, open_topic))]


def test_feed_roundtrip_preserves_episodes(tmp_path):
    cache = JsonCache(_settings(tmp_path))
    episodes = _episodes()
    cache.save_feed(episodes)
    assert cache.load_feed() == episodes  # frozen dataclasses compare by value


def test_expired_feed_is_treated_as_absent(tmp_path):
    cache = JsonCache(_settings(tmp_path, feed_max_age_hours=0.0))
    cache.save_feed(_episodes())
    assert cache.load_feed() is None


def test_corrupt_feed_is_treated_as_absent(tmp_path):
    settings = _settings(tmp_path)
    settings.cache_dir.mkdir(parents=True)
    settings.feed_cache_file.write_text("{not json", encoding="utf-8")
    assert JsonCache(settings).load_feed() is None


def test_missing_feed_is_absent(tmp_path):
    assert JsonCache(_settings(tmp_path)).load_feed() is None


def test_episode_audio_path_is_stable_and_guid_scoped(tmp_path):
    cache = JsonCache(_settings(tmp_path))
    assert cache.episode_audio_path("guid-1") == cache.episode_audio_path("guid-1")
    assert cache.episode_audio_path("guid-1") != cache.episode_audio_path("guid-2")
    assert cache.episode_audio_path("guid-1").suffix == ".mp3"


def test_is_episode_downloaded_requires_a_non_empty_file(tmp_path):
    settings = _settings(tmp_path)
    cache = JsonCache(settings)
    assert not cache.is_episode_downloaded("guid-1")
    settings.episodes_dir.mkdir(parents=True)
    path = cache.episode_audio_path("guid-1")
    path.write_bytes(b"")
    assert not cache.is_episode_downloaded("guid-1")  # empty = failed download
    path.write_bytes(b"mp3")
    assert cache.is_episode_downloaded("guid-1")


def test_clear_deletes_everything_and_reports_counts(tmp_path):
    settings = _settings(tmp_path)
    cache = JsonCache(settings)
    cache.save_feed(_episodes())
    settings.episodes_dir.mkdir(parents=True)
    cache.episode_audio_path("guid-1").write_bytes(b"12345")
    files, size = cache.clear()
    assert files == 2 and size > 0
    assert not settings.cache_dir.exists()


if __name__ == "__main__":
    import tempfile

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        with tempfile.TemporaryDirectory() as tmp:
            fn(Path(tmp))
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
