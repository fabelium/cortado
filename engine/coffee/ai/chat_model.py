"""Chat model port (Strategy/Adapter).

``ChatModel`` is the minimal port the application needs from a large language
model: turn a system instruction + user prompt into text. Keeping it this small
means a local backend (Ollama) and an API backend (Gemini) are interchangeable,
and higher-level features (relevance classification now; RAG chat and book
summaries later) are built on top of this one method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ChatModel(ABC):
    """Port: a text-in/text-out language model."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Stable identifier of the underlying model."""
        raise NotImplementedError

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None) -> str:
        """Return the model's completion for ``prompt`` (optionally guided by
        a ``system`` instruction)."""
        raise NotImplementedError
