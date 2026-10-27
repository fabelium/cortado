"""PassageChunker: split a fragment transcript into overlapping passages, each
tagged with its source metadata (episode, date, topic, fragment id). Written
test-first; pure logic, no external deps. Run: python3 tests/test_passage_chunker.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.knowledge.chunker import PassageChunker


def _fragment(number=237, name="Insight en Marte", start=300, end=480):
    topic = Topic(name=name, time_range=TimeRange(start=start, end=end))
    episode = Episode(f"guid{number}", f"Ep{number}: x", datetime(2019, 10, 17),
                      "http://audio", (topic,))
    return Fragment(episode=episode, topic=topic)


def _words(n):
    return " ".join(f"w{i}" for i in range(n))


def test_short_transcript_is_a_single_passage():
    chunker = PassageChunker(target_words=10, overlap_words=3)
    passages = chunker.chunk(_fragment(), "tres palabras solo")
    assert len(passages) == 1
    assert passages[0].text == "tres palabras solo"
    assert passages[0].index == 0


def test_empty_transcript_yields_no_passages():
    chunker = PassageChunker(target_words=10, overlap_words=3)
    assert chunker.chunk(_fragment(), "") == []
    assert chunker.chunk(_fragment(), "   ") == []


def test_long_transcript_splits_with_overlap():
    chunker = PassageChunker(target_words=10, overlap_words=3)
    passages = chunker.chunk(_fragment(), _words(25))
    # step = target - overlap = 7 -> windows start at 0, 7, 14, 21 -> 4 passages.
    assert len(passages) == 4
    assert [p.index for p in passages] == [0, 1, 2, 3]
    # Consecutive passages share `overlap` words.
    first = passages[0].text.split()
    second = passages[1].text.split()
    assert first[-3:] == second[:3]
    # Last window holds the tail (words 21..24).
    assert passages[-1].text.split() == ["w21", "w22", "w23", "w24"]


def test_passage_carries_fragment_metadata():
    chunker = PassageChunker(target_words=10, overlap_words=3)
    passage = chunker.chunk(_fragment(), "hola")[0]
    assert passage.fragment_id == "ep237@300-480"
    assert passage.episode == 237
    assert passage.date == "2019-10-17"
    assert passage.topic == "Insight en Marte"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
