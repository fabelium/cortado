"""FeedSource: parses RSS items into Episodes via the real DescriptionParser,
skipping items without an audio enclosure or without parseable topics.
Run: python3 tests/test_feed_source.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.config import Settings
from coffee.feed.feed_source import FeedSource
from coffee.parsing.description_parser import DescriptionParser

_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Coffee Break</title>
<item>
  <title>Ep237: Marte y agujeros</title>
  <guid>guid-237</guid>
  <pubDate>Thu, 17 Oct 2019 10:00:00 GMT</pubDate>
  <description>-Insight en Marte (00:00)&lt;br&gt;-Agujeros negros (35:40)</description>
  <enclosure url="http://cdn/ep237.mp3" type="audio/mpeg" length="1"/>
</item>
<item>
  <title>Sin audio</title>
  <guid>guid-no-audio</guid>
  <description>-Algo (00:00)</description>
</item>
<item>
  <title>Sin temas</title>
  <guid>guid-no-topics</guid>
  <description>charla sin timestamps</description>
  <enclosure url="http://cdn/x.mp3" type="audio/mpeg" length="1"/>
</item>
</channel></rss>"""


class _FakeHttp:
    def __init__(self, body):
        self._body = body
        self.urls = []

    def get(self, url, *, stream=False):
        self.urls.append(url)
        return SimpleNamespace(content=self._body)


def _fetch(xml=_RSS):
    settings = Settings()
    http = _FakeHttp(xml.encode("utf-8"))
    episodes = FeedSource(settings, http, DescriptionParser()).fetch()
    return episodes, http, settings


def test_parses_items_into_episodes_with_chained_topics():
    episodes, http, settings = _fetch()
    assert http.urls == [settings.feed_url]
    assert len(episodes) == 1  # the two defective items are skipped
    episode = episodes[0]
    assert episode.guid == "guid-237"
    assert episode.title == "Ep237: Marte y agujeros"
    assert episode.audio_url == "http://cdn/ep237.mp3"
    assert episode.date == datetime(2019, 10, 17, 10, 0, tzinfo=timezone.utc)
    assert [t.name for t in episode.topics] == ["Insight en Marte", "Agujeros negros"]
    assert episode.topics[0].end == 2140  # chained to the next topic's start
    assert episode.topics[-1].end is None  # last topic stays open


def test_items_without_audio_or_topics_are_skipped():
    episodes, _http, _settings = _fetch()
    assert [e.guid for e in episodes] == ["guid-237"]


def test_unreadable_date_falls_back_to_the_epoch():
    xml = _RSS.replace("Thu, 17 Oct 2019 10:00:00 GMT", "not a date")
    episodes, _http, _settings = _fetch(xml)
    assert episodes[0].date == datetime(1970, 1, 1, tzinfo=timezone.utc)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
