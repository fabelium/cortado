"""Shared text helpers for search."""

from __future__ import annotations

import unicodedata


def normalize(text: str) -> str:
    """Lowercase and strip diacritics: 'Agüeros NEGROS' -> 'agueros negros'."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))
