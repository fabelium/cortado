"""Embedding provider port (Strategy/Adapter).

``EmbeddingProvider`` is the port the semantic search depends on. It separates
``embed_documents`` from ``embed_query`` because several backends treat the two
asymmetrically (e.g. Gemini uses distinct ``task_type`` values, and E5-style
models expect different prefixes). Symmetric models simply implement both the
same way.

Vectors are plain ``list[float]`` so the port leaks no vendor types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

Vector = list[float]


class EmbeddingProvider(ABC):
    """Port: maps text to dense vectors for semantic similarity."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Stable identifier of the model, used to namespace the vector cache."""
        raise NotImplementedError

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[Vector]:
        """Embed a batch of documents (the corpus to be searched)."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> Vector:
        """Embed a single search query."""
        raise NotImplementedError
