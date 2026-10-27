"""LLM-based relevance classifier (built on the ChatModel port).

Given a user query and a list of candidate topic names, it asks the model which
ones genuinely belong, returning an include/exclude decision plus a short reason
per candidate. Candidates are judged in a single batched prompt (one API call)
and the model is forced to answer as JSON, which is parsed defensively: any
unparseable answer degrades to "keep everything" so a model hiccup never silently
drops fragments.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from coffee.ai.chat_model import ChatModel
from coffee.domain.errors import AiProviderError

_SYSTEM = (
    "You are a precise research assistant for a Spanish science podcast. "
    "Given a search topic and a numbered list of episode segment titles, decide "
    "which segments are genuinely about that topic. Be inclusive with clearly "
    "related subtopics, but exclude incidental mentions. Answer ONLY with a JSON "
    "array; each item: {\"i\": <index>, \"keep\": <true|false>, \"reason\": "
    "\"<short reason in Spanish>\"}."
)


@dataclass(frozen=True)
class Verdict:
    """The model's decision for one candidate."""

    keep: bool
    reason: str


class RelevanceClassifier:
    """Filters candidate topics by relevance using an injected ChatModel."""

    def __init__(self, chat_model: ChatModel) -> None:
        self._chat = chat_model

    def classify(self, query: str, titles: list[str]) -> list[Verdict]:
        """Return a Verdict per title (same order). Falls back to keep-all."""
        if not titles:
            return []
        numbered = "\n".join(f"{i}. {title}" for i, title in enumerate(titles))
        prompt = f"Topic: {query}\n\nSegments:\n{numbered}"
        try:
            raw = self._chat.complete(prompt, system=_SYSTEM)
        except AiProviderError:
            # Graceful degradation: if the model is unavailable, keep everything.
            return [Verdict(True, "sin clasificar") for _ in titles]
        return self._parse(raw, len(titles))

    @staticmethod
    def _parse(raw: str, count: int) -> list[Verdict]:
        """Parse the JSON array defensively; unknown entries default to keep."""
        verdicts = [Verdict(True, "sin clasificar") for _ in range(count)]
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return verdicts
        try:
            items = json.loads(match.group(0))
        except json.JSONDecodeError:
            return verdicts
        for item in items:
            try:
                index = int(item["i"])
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= index < count:
                verdicts[index] = Verdict(
                    keep=bool(item.get("keep", True)),
                    reason=str(item.get("reason", "")).strip() or "sin motivo",
                )
        return verdicts
