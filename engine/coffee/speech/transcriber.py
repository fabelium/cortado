"""Transcription port and its faster-whisper adapter (Port/Adapter pattern).

``Transcriber`` is the port. ``FasterWhisperTranscriber`` is the adapter backed
by faster-whisper (the 'base' model, Spanish). It writes two files next to the
audio: a ``.txt`` (running text) and a ``.srt`` (with SRT timestamps). The model
is loaded lazily and reused across calls; that single in-process cache is the one
intentional, documented module-level singleton in the codebase. The first run
downloads the 'base' model (~140 MB).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from coffee.domain.errors import TranscriptionError

MODEL_SIZE = "base"


def _format_srt_timestamp(seconds: float) -> str:
    """3661.5 -> '01:01:01,500' (SRT time format)."""
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class Transcriber(ABC):
    """Port: transcribe ``audio_path`` and write transcript files next to it."""

    @abstractmethod
    def transcribe(self, audio_path: Path, *, language: str = "es") -> dict[str, Path]:
        raise NotImplementedError


class FasterWhisperTranscriber(Transcriber):
    """Adapter for the Transcriber port using faster-whisper (lazy model load)."""

    # Lazily loaded and reused across instances/calls: loading the model is
    # expensive, so this documented singleton avoids repeated cold starts.
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as error:
                raise TranscriptionError(
                    "faster-whisper is not installed (pip install faster-whisper)."
                ) from error
            cls._model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        return cls._model

    def transcribe(self, audio_path: Path, *, language: str = "es") -> dict[str, Path]:
        """Transcribe ``audio_path`` and write ``.txt`` + ``.srt`` beside it."""
        model = self._get_model()
        try:
            segments, _info = model.transcribe(str(audio_path), language=language)
            txt_lines: list[str] = []
            srt_blocks: list[str] = []
            for index, segment in enumerate(segments, 1):
                text = segment.text.strip()
                txt_lines.append(text)
                srt_blocks.append(
                    f"{index}\n"
                    f"{_format_srt_timestamp(segment.start)} --> "
                    f"{_format_srt_timestamp(segment.end)}\n"
                    f"{text}\n"
                )
        except TranscriptionError:
            raise
        except Exception as error:  # model/decoding failures
            raise TranscriptionError(
                f"Failed to transcribe {audio_path.name}: {error}"
            ) from error

        txt_path = audio_path.with_suffix(".txt")
        srt_path = audio_path.with_suffix(".srt")
        txt_path.write_text("\n".join(txt_lines) + "\n", encoding="utf-8")
        srt_path.write_text("\n".join(srt_blocks), encoding="utf-8")
        return {"txt": txt_path, "srt": srt_path}
