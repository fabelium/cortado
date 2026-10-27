"""Parser tests. Run with: python3 -m pytest tests/ -q
or directly: python3 tests/test_parsing.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.parsing.description_parser import DescriptionParser, parse_timestamp

_parser = DescriptionParser()


def extract_topics(description):
    return _parser.parse(description)


def test_parse_timestamp_variants():
    assert parse_timestamp("00:00") == 0
    assert parse_timestamp("35:40") == 2140
    assert parse_timestamp("1:09:00") == 4140


def test_bullets_one_per_line_with_hours():
    desc = (
        "-The vibrations (00:00)<br>"
        "-Dispensing parasites (35:40)<br>"
        "-The X-Ray Dot (58:00)<br>"
        "-Supermassive holes (1:09:00)"
    )
    topics = extract_topics(desc)
    assert [t.name for t in topics] == [
        "The vibrations",
        "Dispensing parasites",
        "The X-Ray Dot",          # the inner hyphen is preserved
        "Supermassive holes",
    ]
    assert [t.start for t in topics] == [0, 2140, 3480, 4140]
    # The 'end' chains with the next one; the last stays open.
    assert topics[0].end == 2140
    assert topics[-1].end is None


def test_inner_parentheses_in_name():
    desc = "-The April fools papers (April's fools) (11:00)"
    topics = extract_topics(desc)
    assert len(topics) == 1
    assert topics[0].name == "The April fools papers (April's fools)"
    assert topics[0].start == 660


def test_semicolon_separated_with_side_and_intro():
    desc = (
        "The chat. En el episodio de hoy:Cara A:Book day (5:00); "
        "Moon Knight (8:00); (Semi)automatic puzzles (34:30)"
    )
    topics = extract_topics(desc)
    assert [t.name for t in topics] == [
        "Book day",
        "Moon Knight",
        "(Semi)automatic puzzles",   # inner parenthesis preserved
    ]
    assert [t.start for t in topics] == [300, 480, 2070]


def test_min_prefix_inside_parens():
    topics = extract_topics("-Book day and calendars (min 5:00)")
    assert topics[0].start == 300


def test_sponsor_tail_is_ignored():
    desc = "-Single topic (21:40) Este episodio está patrocinado por X. Hosted on Acast."
    topics = extract_topics(desc)
    assert len(topics) == 1
    assert topics[0].name == "Single topic"


def test_no_timestamps_returns_empty():
    assert extract_topics("Bonus audio. Interview without timestamps.") == []
    assert extract_topics(None) == []
    assert extract_topics("") == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
