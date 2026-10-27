"""Gemini chat adapter (Google Generative Language API, free tier).

REST-based (``requests``) to avoid a heavy SDK. Requires an API key (env
``GEMINI_API_KEY`` or ``GOOGLE_API_KEY``); wired but inactive until a key is set.
"""

from __future__ import annotations

import requests

from coffee.ai.chat_model import ChatModel
from coffee.domain.errors import AiProviderError

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"


class GeminiChatModel(ChatModel):
    """Adapter: text generation via the Gemini API."""

    def __init__(self, api_key: str, model_name: str = "models/gemini-2.0-flash",
                 timeout: int = 30) -> None:
        if not api_key:
            raise AiProviderError(
                "Gemini chat needs an API key (set GEMINI_API_KEY)."
            )
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout

    @property
    def model_id(self) -> str:
        return self._model_name

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        url = _ENDPOINT.format(model=self._model_name)
        payload: dict = {"contents": [{"parts": [{"text": prompt}]}]}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        try:
            response = requests.post(
                url, headers={"x-goog-api-key": self._api_key},
                json=payload, timeout=self._timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (requests.RequestException, KeyError, IndexError, ValueError) as error:
            raise AiProviderError(f"Gemini chat request failed: {error}") from error
