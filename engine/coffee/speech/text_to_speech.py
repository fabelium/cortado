"""Text-to-speech port and its gTTS adapter (Port/Adapter pattern).

``TextToSpeech`` is the port. ``GttsTextToSpeech`` is the adapter backed by
Google's gTTS (Spanish voice). gTTS needs internet access; on any failure it
raises ``TtsError`` so the caller can degrade gracefully and still ship the
MP3 without spoken announcements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from coffee.domain.errors import TtsError


class TextToSpeech(ABC):
    """Port: synthesize ``text`` into an audio file at ``dest``."""

    @abstractmethod
    def synthesize(self, text: str, dest: Path) -> Path:
        raise NotImplementedError


class GttsTextToSpeech(TextToSpeech):
    """Adapter for the TextToSpeech port using gTTS (Spanish, ``lang="es"``)."""

    def __init__(self, language: str = "es") -> None:
        self._language = language

    def synthesize(self, text: str, dest: Path) -> Path:
        """Generate an MP3 announcement of ``text``. Returns ``dest``."""
        try:
            from gtts import gTTS
        except ImportError as error:
            raise TtsError("gTTS is not installed (pip install gTTS).") from error

        try:
            gTTS(text=text, lang=self._language, slow=False).save(str(dest))
        except Exception as error:  # gTTS wraps network errors in many types
            raise TtsError(f"Could not generate the announcement: {error}") from error
        return dest
