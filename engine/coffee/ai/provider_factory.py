"""Provider factory (Factory pattern).

Resolves a provider *name* into a concrete adapter, hiding construction details
(API keys, model ids) from the composition root. Adding a new backend (Ollama,
Mistral, Cohere...) means adding one branch here and nothing else changes.

Supported names:
* embeddings: ``local`` (fastembed, default), ``gemini``
* chat:       ``gemini`` (``local``/Ollama is a documented future extension)
"""

from __future__ import annotations

import os

from coffee.ai.chat_model import ChatModel
from coffee.ai.embedding_provider import EmbeddingProvider
from coffee.config import Settings
from coffee.domain.errors import AiProviderError


def _gemini_api_key() -> str:
    """Read the Gemini key from either common environment variable."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""


class ProviderFactory:
    """Builds embedding and chat adapters from a provider name."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def embedding_provider(self, name: str) -> EmbeddingProvider:
        name = (name or "local").lower()
        if name == "local":
            from coffee.ai.fastembed_provider import FastEmbedEmbeddingProvider

            return FastEmbedEmbeddingProvider(self._settings.embedding_model_local)
        if name == "gemini":
            from coffee.ai.gemini_embedding import GeminiEmbeddingProvider

            return GeminiEmbeddingProvider(
                _gemini_api_key(), self._settings.embedding_model_gemini
            )
        raise AiProviderError(f"Unknown embedding provider: '{name}'.")

    def chat_model(self, name: str) -> ChatModel:
        name = (name or "gemini").lower()
        if name == "gemini":
            from coffee.ai.gemini_chat import GeminiChatModel

            return GeminiChatModel(_gemini_api_key(), self._settings.chat_model_gemini)
        raise AiProviderError(
            f"Unknown chat provider: '{name}'. Only 'gemini' is wired so far."
        )
