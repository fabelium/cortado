"""Domain exception hierarchy.

A single base (``CoffeeError``) lets the composition root catch every
*expected* failure of the tool while letting genuine bugs propagate. Each
subclass marks the layer/port that failed, so callers can degrade gracefully
(a failed TTS, e-mail or transcription must never abort an already-built MP3).
"""

from __future__ import annotations


class CoffeeError(Exception):
    """Base class for all controlled errors raised by the tool."""


class NetworkError(CoffeeError):
    """A network call failed after exhausting retries."""


class AudioError(CoffeeError):
    """An ffmpeg cut/concat/probe operation failed."""


class MailError(CoffeeError):
    """Sending the result by e-mail failed."""


class TtsError(CoffeeError):
    """Generating a text-to-speech announcement failed."""


class TranscriptionError(CoffeeError):
    """Transcribing the generated audio failed."""


class AiProviderError(CoffeeError):
    """An AI provider (embeddings or chat model) failed or is misconfigured."""
