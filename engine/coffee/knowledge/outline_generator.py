"""Propose a didactic book outline from the selection's full transcripts.

The curated selection is bounded, so its transcripts fit in context: the chat
model sees them whole and returns a JSON index (chapters -> section titles),
which is parsed into a BookOutline. A malformed reply is a controlled error.
"""

from __future__ import annotations

import json

from coffee.domain.errors import CoffeeError
from coffee.knowledge.book import BookOutline, Chapter

_SYSTEM = (
    "Eres un editor que organiza material divulgativo en un índice didáctico, "
    "ordenado para aprender (no cronológico). Respondes SOLO con JSON válido."
)


class OutlineGenerator:
    """Asks the chat model for a structured outline and parses it."""

    def __init__(self, chat) -> None:
        self._chat = chat

    def propose(self, title: str, transcripts: list[str]) -> BookOutline:
        material = "\n\n".join(transcripts)
        prompt = (
            f"Título del libro: {title}\n\n"
            f"Material de los episodios:\n{material}\n\n"
            'Devuelve SOLO JSON con esta forma: '
            '{"title": "...", "chapters": [{"title": "...", '
            '"sections": ["...", "..."]}]}'
        )
        return self._parse(self._chat.complete(prompt, system=_SYSTEM), title)

    @staticmethod
    def _parse(raw: str, fallback_title: str) -> BookOutline:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[len("json"):]
        try:
            data = json.loads(text)
            chapters = [
                Chapter(chapter["title"], list(chapter["sections"]))
                for chapter in data["chapters"]
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise CoffeeError(f"Could not parse the book outline: {error}")
        return BookOutline(data.get("title", fallback_title), chapters)
