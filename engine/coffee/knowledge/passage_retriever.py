"""Retrieve the passages most relevant to a question (cosine similarity).

The retriever embeds a set of passages once (``index``) and then answers
queries (``retrieve``) by ranking them against the query embedding. It depends
only on the ``EmbeddingProvider`` port, so the same local/Gemini backends used
for search power retrieval too. This is the recall half of the future RAG chat;
generation (citing answers) builds on top of it.
"""

from __future__ import annotations

import numpy as np

from coffee.ai.embedding_provider import EmbeddingProvider
from coffee.knowledge.passage import Passage


class PassageRetriever:
    """In-memory vector index over passages with top-k cosine retrieval."""

    def __init__(self, embeddings: EmbeddingProvider) -> None:
        self._embeddings = embeddings
        self._passages: list[Passage] = []
        self._matrix: np.ndarray | None = None  # row-normalised (n, d)

    def index(self, passages: list[Passage]) -> None:
        """Embed and store ``passages`` (rows are L2-normalised for cosine)."""
        self._passages = list(passages)
        if not self._passages:
            self._matrix = None
            return
        vectors = self._embeddings.embed_documents([p.text for p in self._passages])
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
        self._matrix = matrix / norms

    def retrieve(self, query: str, k: int = 5) -> list[Passage]:
        """Return the ``k`` passages most similar to ``query`` (best first)."""
        if self._matrix is None or not self._passages:
            return []
        query_vector = np.asarray(self._embeddings.embed_query(query), dtype=np.float32)
        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-12)
        scores = self._matrix @ query_vector
        order = np.argsort(scores)[::-1][:k]
        return [self._passages[i] for i in order]
