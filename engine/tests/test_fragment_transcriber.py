"""FragmentTranscriber: the real TranscriptProducer behind the TranscriptStore.

It locates the episode audio, cuts the fragment's time range and transcribes the
cut, returning running text. Fakes for ffmpeg/whisper keep the test free of audio
and models. Run: python3 tests/test_fragment_transcriber.py
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.knowledge.fragment_transcriber import FragmentTranscriber


def _fragment(number=237, name="Insight en Marte", start=300, end=480):
    topic = Topic(name=name, time_range=TimeRange(start=start, end=end))
    episode = Episode(f"guid{number}", f"Ep{number}: x", datetime(2019, 10, 17),
                      "http://audio", (topic,))
    return Fragment(episode=episode, topic=topic)


class _FakeFFmpeg:
    """Records the cut and writes a placeholder file at ``dest`` (no real audio)."""

    def __init__(self):
        self.calls = []

    def cut_fragment(self, src, start, end, dest):
        self.calls.append((src, start, end, dest))
        Path(dest).write_bytes(b"audio")


class _FakeTranscriber:
    """Writes a ``.txt`` beside the audio (like faster-whisper) and records it."""

    def __init__(self, lines):
        self._lines = lines
        self.seen = []

    def transcribe(self, audio_path, *, language="es"):
        self.seen.append(Path(audio_path))
        txt = Path(audio_path).with_suffix(".txt")
        srt = Path(audio_path).with_suffix(".srt")
        txt.write_text("\n".join(self._lines) + "\n", encoding="utf-8")
        srt.write_text("", encoding="utf-8")
        return {"txt": txt, "srt": srt}


def _episode_audio(path="/cache/episodes/ep237.mp3"):
    seen = []

    def resolve(episode):
        seen.append(episode)
        return Path(path)

    resolve.seen = seen
    return resolve


def test_produces_running_transcript_text_for_a_fragment():
    transcriber = _FakeTranscriber(["la sonda Insight", "aterrizó en Marte"])
    produce = FragmentTranscriber(_FakeFFmpeg(), transcriber, _episode_audio())

    text = produce(_fragment())

    # Lines are joined into a single running passage (for chunking), not raw \n.
    assert text == "la sonda Insight aterrizó en Marte"
    # The transcriber was handed the cut file, not the full episode.
    assert transcriber.seen[0].name.endswith(".mp3")


def test_cuts_the_episode_audio_over_the_fragment_time_range():
    ffmpeg = _FakeFFmpeg()
    resolver = _episode_audio("/cache/episodes/ep237.mp3")
    produce = FragmentTranscriber(ffmpeg, _FakeTranscriber(["x"]), resolver)

    fragment = _fragment(start=300, end=480)
    produce(fragment)

    assert len(ffmpeg.calls) == 1
    src, start, end, dest = ffmpeg.calls[0]
    assert src == Path("/cache/episodes/ep237.mp3")
    assert (start, end) == (300, 480)
    assert resolver.seen == [fragment.episode]
    # The cut output is what gets transcribed.
    assert Path(dest).suffix == ".mp3"


def test_does_not_leave_temporary_files_behind():
    ffmpeg = _FakeFFmpeg()
    transcriber = _FakeTranscriber(["algo"])
    produce = FragmentTranscriber(ffmpeg, transcriber, _episode_audio())

    produce(_fragment())

    cut_path = transcriber.seen[0]
    assert not cut_path.exists()                       # cut audio cleaned up
    assert not cut_path.with_suffix(".txt").exists()   # and the transcript file
    assert not cut_path.parent.exists()                # and the temp dir itself


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
