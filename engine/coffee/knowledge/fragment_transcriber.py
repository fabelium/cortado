"""Real ``TranscriptProducer`` for the ``TranscriptStore`` (Adapter pattern).

Turns a ``Fragment`` into its transcript text, which is what the RAG read side
needs. It resolves the episode audio (download/cache, injected), cuts the
fragment's time range with ffmpeg and transcribes that cut, returning a single
running passage. Every collaborator is injected, so this stays free of audio,
whisper and download concerns and is trivial to test with fakes.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable

from coffee.application.fragment_ref import to_id
from coffee.domain.models import Episode, Fragment
from coffee.infrastructure.ffmpeg import FFmpeg
from coffee.speech.transcriber import Transcriber

# Resolves a fragment's episode to a local audio file (cache/download).
EpisodeAudio = Callable[[Episode], Path]


class FragmentTranscriber:
    """Cuts a fragment's audio and transcribes it (the store's real producer)."""

    def __init__(
        self,
        ffmpeg: FFmpeg,
        transcriber: Transcriber,
        episode_audio: EpisodeAudio,
    ) -> None:
        self._ffmpeg = ffmpeg
        self._transcriber = transcriber
        self._episode_audio = episode_audio

    def __call__(self, fragment: Fragment) -> str:
        """Produce the transcript text for ``fragment`` (cut + transcribe)."""
        src = self._episode_audio(fragment.episode)
        tmp_dir = Path(tempfile.mkdtemp(prefix="coffeeclips_tx_"))
        try:
            cut = tmp_dir / f"{to_id(fragment)}.mp3"
            self._ffmpeg.cut_fragment(
                src, fragment.topic.start, fragment.topic.end, cut
            )
            written = self._transcriber.transcribe(cut)
            text = Path(written["txt"]).read_text(encoding="utf-8")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        # Whisper writes one line per segment; join them into running text.
        return " ".join(text.split())
