"""Settings invariants. The spoken Spanish copy must respect the gTTS request
limit: any punctuation-delimited run over ~100 chars gets force-split mid-
phrase, which is heard as a broken, sentence-final pause (live bug: the pause
between "inteligencia" and "artificial" in the disclaimer).
Run: python3 tests/test_config.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.config import Settings

_GTTS_CHUNK_LIMIT = 100  # gTTS max characters per TTS request


def test_disclaimer_segments_fit_in_one_gtts_chunk():
    segments = [
        segment.strip()
        for segment in re.split(r"[.,;:]", Settings().disclaimer_text)
        if segment.strip()
    ]
    too_long = [s for s in segments if len(s) > _GTTS_CHUNK_LIMIT]
    assert not too_long, f"gTTS will split these mid-phrase: {too_long}"


def test_podcast_name_fits_in_one_gtts_chunk():
    assert len(Settings().podcast_name) <= _GTTS_CHUNK_LIMIT


def test_tts_tempo_out_of_ffmpeg_range_is_rejected():
    # ffmpeg's atempo only accepts 0.5-2.0; outside it the announcement would
    # fail to encode and silently vanish from the clip.
    for bad in (0.0, -1.0, 0.4, 2.5):
        try:
            Settings(tts_tempo=bad)
        except ValueError:
            continue
        raise AssertionError(f"tts_tempo={bad} should be rejected")


def test_tts_tempo_in_range_is_accepted():
    assert Settings(tts_tempo=0.5).tts_tempo == 0.5
    assert Settings(tts_tempo=2.0).tts_tempo == 2.0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
