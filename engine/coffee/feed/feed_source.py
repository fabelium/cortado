"""RSS feed source.

``FeedSource`` downloads the RSS via the ``HttpClient`` and parses it with
feedparser into domain ``Episode`` objects, delegating the messy timestamp
extraction to a ``DescriptionParser``. Items without audio or without parseable
topics are skipped: they add nothing to a search and keep the cache light.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from coffee.config import Settings
from coffee.domain.models import Episode
from coffee.infrastructure.http_client import HttpClient
from coffee.parsing.description_parser import DescriptionParser


class FeedSource:
    """Fetches and parses the podcast RSS into domain episodes."""

    def __init__(
        self,
        settings: Settings,
        http_client: HttpClient,
        parser: DescriptionParser,
    ) -> None:
        self._settings = settings
        self._http = http_client
        self._parser = parser

    def fetch(self) -> list[Episode]:
        """Download and parse the feed into a list of episodes."""
        raw_xml = self._http.get(self._settings.feed_url).content
        return self._parse(raw_xml)

    @staticmethod
    def _entry_date(entry) -> datetime:
        """Robust publication date; falls back to the epoch if unreadable."""
        if getattr(entry, "published_parsed", None):
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        published = entry.get("published")
        if published:
            try:
                return parsedate_to_datetime(published)
            except (TypeError, ValueError):
                pass
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

    @staticmethod
    def _entry_audio_url(entry) -> str | None:
        """Extract the MP3 enclosure URL from an item."""
        for enclosure in entry.get("enclosures", []):
            href = enclosure.get("href") or enclosure.get("url")
            if href:
                return href
        for link in entry.get("links", []):
            if link.get("rel") == "enclosure" and link.get("href"):
                return link["href"]
        return None

    def _parse(self, raw_xml: bytes) -> list[Episode]:
        parsed = feedparser.parse(raw_xml)
        episodes: list[Episode] = []
        for entry in parsed.entries:
            audio_url = self._entry_audio_url(entry)
            if not audio_url:
                continue
            topics = self._parser.parse(
                entry.get("description") or entry.get("summary")
            )
            if not topics:
                continue
            guid = entry.get("id") or entry.get("guid") or audio_url
            episodes.append(
                Episode(
                    guid=guid,
                    title=entry.get("title", "(untitled)"),
                    date=self._entry_date(entry),
                    audio_url=audio_url,
                    topics=tuple(topics),
                )
            )
        return episodes
