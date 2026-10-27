"""Extracting topics and timestamps from an RSS item description.

``DescriptionParser`` is a *pure* text -> ``Topic`` transformer: no I/O, easily
unit-testable. The episode descriptions are wildly irregular, so the parser is
deliberately defensive:

- Sometimes each topic sits on its own bulleted line: ``-Topic (mm:ss)``.
- Sometimes ALL topics share a single line, separated by ``;`` or by bullets.
- Names may contain their own parentheses: ``April's fools papers (11:00)``.
- Names may contain inner hyphens: ``The X-Ray Dot (58:00)``.
- There are filler prefixes: ``En el episodio de hoy:``, ``Cara A:``, ``Cara B:``.
- The time may be ``(mm:ss)``, ``(h:mm:ss)`` or carry a ``min`` prefix: ``(min 5:00)``.
- A sponsor / Acast tail usually trails the real content and must be dropped.

Robust strategy: instead of splitting on separators (fragile because of the
inner hyphens), we use the TIMESTAMPS as anchors. A topic name is the text
between the end of the previous timestamp and the start of its own. This isolates
each name without breaking inner hyphens or parentheses.
"""

from __future__ import annotations

import html
import re

from coffee.domain.models import TimeRange, Topic

# A timestamp: inside parentheses, optional "min", mm:ss or h:mm:ss.
_TIME_RE = re.compile(r"\(\s*(?:min\.?\s*)?(\d{1,2}:\d{2}(?::\d{2})?)\s*\)")

# Trailing text to discard (sponsorship / Acast notice) up to the end.
_TAIL_RE = re.compile(
    r"(?:Hosted on Acast|Este episodio (?:está|es |cuenta|contiene|incluye)).*$",
    re.IGNORECASE | re.DOTALL,
)

# Filler introduction before the first topic.
_INTRO_RE = re.compile(
    r"(?i)^.*?\b(?:en el episodio de hoy|programa de hoy)\s*:?\s*"
)

# "Cara A:" / "Cara B:" markers are treated as topic separators.
_SIDE_RE = re.compile(r"(?i)\bcara\s+[ab]\s*:?\s*")

# Defensive cap: a "name" longer than this is almost certainly junk/filler.
_MAX_NAME_LEN = 160


def parse_timestamp(timestamp: str) -> int:
    """'35:40' -> 2140 ; '1:09:00' -> 4140. Raises ValueError when invalid."""
    parts = timestamp.split(":")
    try:
        numbers = [int(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"non-numeric timestamp: {timestamp!r}") from exc
    if len(parts) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = numbers
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"unsupported timestamp format: {timestamp!r}")


class DescriptionParser:
    """Pure parser: RSS description text -> ordered list of ``Topic``.

    Stateless, so a single shared instance is safe to reuse.
    """

    @staticmethod
    def _strip_html(description: str) -> str:
        """Turn an HTML description into plain text with useful line breaks."""
        text = re.sub(r"<\s*br\s*/?\s*>", "\n", description, flags=re.IGNORECASE)
        text = re.sub(r"</\s*p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<\s*li[^>]*>", "\n-", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return html.unescape(text)

    @staticmethod
    def _clean_name(raw: str) -> str:
        """Clean a topic name: drop leading separators and filler."""
        raw = raw.strip()
        # If a stray ";" remains, the name is whatever follows the last one.
        if ";" in raw:
            raw = raw.rsplit(";", 1)[-1]
        # Strip leading bullets and punctuation.
        raw = re.sub(r"^[\-–—•\*\s:;]+", "", raw)
        return raw.strip(" .;:–—-")

    def parse(self, description: str | None) -> list[Topic]:
        """Return the episode's topics with their ``end`` already resolved.

        Each topic's ``end`` is the next topic's ``start``; the last one's ``end``
        stays ``None``. If the description holds no valid timestamps, returns [].
        """
        if not description:
            return []

        text = self._strip_html(description)
        text = _TAIL_RE.sub("", text)
        text = re.sub(r"\s+", " ", text)       # collapse newlines and repeated spaces
        text = _INTRO_RE.sub("", text)         # drop the filler intro
        text = _SIDE_RE.sub(" ; ", text)       # "Cara A:" becomes a separator

        raw: list[tuple[str, int]] = []
        cursor = 0
        for match in _TIME_RE.finditer(text):
            name = self._clean_name(text[cursor:match.start()])
            cursor = match.end()
            if not name or len(name) > _MAX_NAME_LEN:
                continue
            try:
                start = parse_timestamp(match.group(1))
            except ValueError:
                continue
            raw.append((name, start))

        # Sort by time (in case the description is out of order) and resolve each
        # topic's end as the next topic's start.
        raw.sort(key=lambda item: item[1])
        topics: list[Topic] = []
        for index, (name, start) in enumerate(raw):
            end = raw[index + 1][1] if index + 1 < len(raw) else None
            topics.append(Topic(name=name, time_range=TimeRange(start=start, end=end)))
        return topics
