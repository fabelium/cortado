"""Local embedding adapter backed by fastembed (ONNX, no PyTorch).

This is the zero-cost, offline default. The multilingual MiniLM model handles
Spanish well and is symmetric (no query/document prefixes), so both embedding
methods share one code path. The model is loaded lazily and reused across calls
(a documented singleton-per-instance), because loading it is the slow part.
"""

from __future__ import annotations

from coffee.ai.embedding_provider import EmbeddingProvider, Vector
from coffee.domain.errors import AiProviderError

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class FastEmbedEmbeddingProvider(EmbeddingProvider):
    """Adapter: local sentence-embeddings via fastembed."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._model_name = model_name
        self._model = None  # lazy: created on first use, then reused

    @property
    def model_id(self) -> str:
        return self._model_name

    def _ensure_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
            except ImportError as error:  # pragma: no cover - environment guard
                raise AiProviderError(
                    "fastembed is not installed (pip install fastembed)."
                ) from error
            try:
                self._model = TextEmbedding(model_name=self._model_name)
            except Exception as error:  # model download / init failure
                raise AiProviderError(
                    f"Could not load local model '{self._model_name}': {error}"
                ) from error
        return self._model

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        model = self._ensure_model()
        # fastembed yields numpy arrays; convert to plain lists at the boundary.
        return [vector.tolist() for vector in model.embed(texts)]

    def embed_query(self, text: str) -> Vector:
        # Symmetric model: a query is embedded exactly like a document.
        return self.embed_documents([text])[0]
