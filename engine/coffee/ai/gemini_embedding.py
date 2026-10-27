"""Gemini embedding adapter (Google Generative Language API, free tier).

Implemented over the REST endpoint with ``requests`` to avoid a heavyweight SDK
dependency. Documents and queries use the proper ``task_type`` so retrieval
quality matches Google's recommendation. Requires an API key (env
``GEMINI_API_KEY`` or ``GOOGLE_API_KEY``); wired but inactive until a key is set.
"""

from __future__ import annotations

import requests

from coffee.ai.embedding_provider import EmbeddingProvider, Vector
from coffee.domain.errors import AiProviderError

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/{model}:embedContent"


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Adapter: embeddings via the Gemini API."""

    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004",
                 timeout: int = 30) -> None:
        if not api_key:
            raise AiProviderError(
                "Gemini embeddings need an API key (set GEMINI_API_KEY)."
            )
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout

    @property
    def model_id(self) -> str:
        return self._model_name

    def _embed(self, text: str, task_type: str) -> Vector:
        url = _ENDPOINT.format(model=self._model_name)
        payload = {
            "model": self._model_name,
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        try:
            response = requests.post(
                url, headers={"x-goog-api-key": self._api_key},
                json=payload, timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()["embedding"]["values"]
        except (requests.RequestException, KeyError, ValueError) as error:
            raise AiProviderError(f"Gemini embedding request failed: {error}") from error

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        return [self._embed(text, "RETRIEVAL_DOCUMENT") for text in texts]

    def embed_query(self, text: str) -> Vector:
        return self._embed(text, "RETRIEVAL_QUERY")
