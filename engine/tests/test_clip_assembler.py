"""ClipAssembler: downloads each episode once, always builds oldest-first,
degrades gracefully when TTS fails, prepends the disclaimer per output file and
packs whole units into split blocks. All ports are injected fakes; the real
AnnouncementBuilder and JsonCache run against a temp Settings.
Run: python3 tests/test_clip_assembler.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.application.clip_assembler import ClipAssembler
from coffee.config import Settings
from coffee.domain.errors import TtsError
from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.infrastructure.json_cache import JsonCache
from coffee.speech.announcements import AnnouncementBuilder


class _FakeFFmpeg:
    def __init__(self):
        self.cut_calls = []     # (src, start, end, dest)
        self.concat_calls = []  # (parts, dest)

    def make_silence(self, seconds, dest):
        dest.write_bytes(b"silence")

    def to_uniform_mp3(self, src, dest, tempo=None):
        self.tempos = getattr(self, "tempos", []) + [tempo]
        dest.write_bytes(src.read_bytes())

    def cut_fragment(self, src, start, end, dest):
        self.cut_calls.append((src, start, end, dest))
        dest.write_bytes(b"frag")

    def probe_duration(self, path):
        return 10.0  # every part lasts 10s; drives the split packing

    def concat(self, parts, dest):
        self.concat_calls.append((list(parts), dest))
        dest.write_bytes(b"out")


class _FakeDownloader:
    def __init__(self):
        self.urls = []

    def download(self, url, dest, *, progress=None):
        self.urls.append(url)
        dest.write_bytes(b"mp3")
        if progress:
            progress(100, 100)


class _FakeTts:
    def __init__(self, fail=False):
        self.fail = fail
        self.texts = []

    def synthesize(self, text, dest):
        if self.fail:
            raise TtsError("no voice available")
        self.texts.append(text)
        dest.write_bytes(b"tts")


def _settings(tmp_path):
    return Settings(
        cache_dir=tmp_path / "cache",
        episodes_dir=tmp_path / "cache" / "episodes",
        feed_cache_file=tmp_path / "cache" / "feed_cache.json",
        output_dir=tmp_path / "output",
    )


def _assembler(tmp_path, tts=None):
    settings = _settings(tmp_path)
    ffmpeg = _FakeFFmpeg()
    downloader = _FakeDownloader()
    assembler = ClipAssembler(
        settings=settings,
        ffmpeg=ffmpeg,
        downloader=downloader,
        text_to_speech=tts or _FakeTts(),
        announcements=AnnouncementBuilder(settings),
        cache=JsonCache(settings),
    )
    return assembler, ffmpeg, downloader


def _fragment(guid, day, title=None):
    topic = Topic(name=f"tema {guid}", time_range=TimeRange(start=30, end=90))
    episode = Episode(
        guid, title or f"Ep{day}: x", datetime(2019, 10, day),
        f"http://cdn/{guid}.mp3", (topic,),
    )
    return Fragment(episode=episode, topic=topic)


def _assemble(assembler, fragments, out, **overrides):
    options = dict(keep_temp=False, intro=False, disclaimer=False,
                   split_seconds=None)
    options.update(overrides)
    return assembler.assemble(fragments, out, **options)


def test_downloads_each_distinct_episode_once(tmp_path):
    assembler, _ffmpeg, downloader = _assembler(tmp_path)
    shared = _fragment("guid-a", 1)
    twin = Fragment(episode=shared.episode, topic=shared.topic)
    _assemble(assembler, [shared, twin, _fragment("guid-b", 2)],
              tmp_path / "out.mp3")
    assert sorted(downloader.urls) == [
        "http://cdn/guid-a.mp3", "http://cdn/guid-b.mp3"
    ]


def test_output_is_chronological_even_if_input_is_not(tmp_path):
    assembler, ffmpeg, _downloader = _assembler(tmp_path)
    newest, oldest = _fragment("guid-new", 20), _fragment("guid-old", 3)
    _assemble(assembler, [newest, oldest], tmp_path / "out.mp3")
    cut_sources = [src.name for src, *_ in ffmpeg.cut_calls]
    cache = JsonCache(_settings(tmp_path))
    assert cut_sources == [
        cache.episode_audio_path("guid-old").name,
        cache.episode_audio_path("guid-new").name,
    ]


def test_intro_prepends_pause_and_announcement_per_fragment(tmp_path):
    tts = _FakeTts()
    assembler, ffmpeg, _downloader = _assembler(tmp_path, tts=tts)
    outputs = _assemble(assembler, [_fragment("guid-a", 17)],
                        tmp_path / "out.mp3", intro=True)
    assert outputs == [tmp_path / "out.mp3"]
    (parts, _dest), = ffmpeg.concat_calls
    names = [p.name for p in parts]
    assert names == ["silence.mp3", "intro_001.mp3", "frag_001.mp3"]
    # the announcement speaks the episode and the Spanish date
    assert "17 de octubre de 2019" in tts.texts[0]


def test_announcements_are_sped_up_to_the_settings_tempo(tmp_path):
    """gTTS speech is slow and robotic; announcements get a tempo boost."""
    assembler, ffmpeg, _downloader = _assembler(tmp_path)
    settings = _settings(tmp_path)
    _assemble(assembler, [_fragment("guid-a", 17)], tmp_path / "out.mp3",
              intro=True, disclaimer=True)
    assert settings.tts_tempo > 1.0
    assert ffmpeg.tempos == [settings.tts_tempo] * 2  # intro + disclaimer


def test_tts_failure_degrades_to_the_bare_fragment(tmp_path):
    assembler, ffmpeg, _downloader = _assembler(tmp_path, tts=_FakeTts(fail=True))
    notes = []
    _assemble(assembler, [_fragment("guid-a", 1)], tmp_path / "out.mp3",
              intro=True, report=notes.append)
    (parts, _dest), = ffmpeg.concat_calls
    assert [p.name for p in parts] == ["frag_001.mp3"]
    assert any("!" in note for note in notes)  # degraded, but reported


def test_disclaimer_opens_every_output_file(tmp_path):
    assembler, ffmpeg, _downloader = _assembler(tmp_path)
    _assemble(assembler, [_fragment("guid-a", 1), _fragment("guid-b", 2)],
              tmp_path / "out.mp3", disclaimer=True,
              split_seconds=10)  # 10s units -> one fragment per block
    assert len(ffmpeg.concat_calls) == 2
    for parts, _dest in ffmpeg.concat_calls:
        assert parts[0].name == "disclaimer.mp3"


def test_split_packs_whole_units_and_suffixes_parts(tmp_path):
    assembler, ffmpeg, _downloader = _assembler(tmp_path)
    fragments = [_fragment("guid-a", 1), _fragment("guid-b", 2),
                 _fragment("guid-c", 3)]
    outputs = _assemble(assembler, fragments, tmp_path / "out.mp3",
                        split_seconds=20)  # 10s units -> blocks of 2 + 1
    assert [o.name for o in outputs] == ["out_parte1.mp3", "out_parte2.mp3"]
    sizes = [len(parts) for parts, _dest in ffmpeg.concat_calls]
    assert sizes == [2, 1]  # whole units, never a fragment cut in half


def test_oversized_unit_gets_its_own_block():
    units = [(["a"], 30.0), (["b"], 5.0), (["c"], 5.0)]
    blocks = ClipAssembler._pack_blocks(units, split_seconds=10)
    assert blocks == [[(["a"], 30.0)], [(["b"], 5.0), (["c"], 5.0)]]


def test_no_split_returns_a_single_block():
    units = [(["a"], 30.0), (["b"], 5.0)]
    assert ClipAssembler._pack_blocks(units, split_seconds=None) == [units]


if __name__ == "__main__":
    import tempfile

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        if "tmp_path" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
            with tempfile.TemporaryDirectory() as tmp:
                fn(Path(tmp))
        else:
            fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
