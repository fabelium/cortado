"""KeywordSearchStrategy: accent/case-insensitive AND matching over topic
names, results always oldest-first. Run: python3 tests/test_keyword_search.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.domain.models import Episode, TimeRange, Topic
from coffee.search.search_strategy import KeywordSearchStrategy


def _episode(guid, day, *topic_names):
    topics = tuple(
        Topic(name=name, time_range=TimeRange(start=i * 100, end=(i + 1) * 100))
        for i, name in enumerate(topic_names)
    )
    return Episode(guid, f"Ep{day}: x", datetime(2019, 10, day),
                   "http://audio", topics)


_EPISODES = [
    _episode("g2", 20, "Agujeros negros supermasivos", "Vacunas y ARN"),
    _episode("g1", 3, "El agujero negro M87"),
]


def test_matching_is_accent_and_case_insensitive():
    hits = KeywordSearchStrategy().search(_EPISODES, "AGUJERO")
    assert [h.topic.name for h in hits] == [
        "El agujero negro M87",           # oldest first
        "Agujeros negros supermasivos",
    ]
    assert KeywordSearchStrategy().search(_EPISODES, "vacúnas")[0].topic.name == (
        "Vacunas y ARN"
    )


def test_all_query_words_must_match():
    hits = KeywordSearchStrategy().search(_EPISODES, "agujero negro")
    assert len(hits) == 2
    assert KeywordSearchStrategy().search(_EPISODES, "agujero marte") == []


def test_blank_query_returns_nothing():
    assert KeywordSearchStrategy().search(_EPISODES, "   ") == []


def test_keyword_hits_carry_no_score():
    hits = KeywordSearchStrategy().search(_EPISODES, "vacunas")
    assert hits[0].score is None and hits[0].reason is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
