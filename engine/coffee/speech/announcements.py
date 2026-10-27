"""Spanish announcement and disclaimer text builder.

``AnnouncementBuilder`` produces the wording that is read aloud before each
fragment: the podcast name, the episode number (when present) and the date in
Spanish. These strings are intentionally Spanish: they are spoken to a
Spanish-speaking audience and must not change. The disclaimer text itself comes
from ``Settings``.
"""

from __future__ import annotations

import re
from datetime import datetime

from coffee.config import Settings
from coffee.domain.models import Episode

# Spanish month names, used to build the spoken date. Kept in Spanish on purpose.
_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# "Ep237", "Ep563_B", "Redifusión: Ep364_B" -> number and, if any, side A/B.
_EPISODE_RE = re.compile(r"\bEp\.?\s*(\d+)(?:[_\s]?([AB]))?", re.IGNORECASE)


def episode_number_label(title: str) -> str:
    """'Ep563_B: ...' -> '563 B' ; 'Bonus: ...' -> '' (no number)."""
    match = _EPISODE_RE.search(title)
    if not match:
        return ""
    number = match.group(1)
    side = match.group(2)
    return f"{number} {side.upper()}" if side else number


def episode_key(title: str) -> str:
    """'Ep563_B: ...' -> '563b' ; 'Ep237: ...' -> '237' ; 'Bonus: ...' -> ''."""
    match = _EPISODE_RE.search(title)
    if not match:
        return ""
    number = match.group(1)
    side = match.group(2)
    return f"{number}{side.lower()}" if side else number


def episode_number(title: str) -> int:
    """'Ep563_B: ...' -> 563 ; 'Bonus: ...' -> 0 (no number)."""
    match = _EPISODE_RE.search(title)
    return int(match.group(1)) if match else 0


def spanish_date(date: datetime) -> str:
    """17/10/2019 -> '17 de octubre de 2019' (Spanish, spoken aloud)."""
    return f"{date.day} de {_MONTHS[date.month - 1]} de {date.year}"


class AnnouncementBuilder:
    """Builds the spoken intro text and exposes the disclaimer from settings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def for_episode(self, episode: Episode) -> str:
        """Spoken text before a fragment: podcast, episode (if any) and date."""
        label = episode_number_label(episode.title)
        date = spanish_date(episode.date)
        if label:
            return f"{self._settings.podcast_name}. Episodio {label}. {date}."
        return f"{self._settings.podcast_name}. {date}."

    @property
    def disclaimer(self) -> str:
        """Educational disclaimer read at the start of each generated file."""
        return self._settings.disclaimer_text
