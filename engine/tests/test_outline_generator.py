"""OutlineGenerator: ask the chat model for a didactic index over the full
transcripts and parse its JSON reply into a BookOutline. A fake chat keeps it
offline. Run: python3 tests/test_outline_generator.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.domain.errors import CoffeeError
from coffee.knowledge.outline_generator import OutlineGenerator


class _FakeChat:
    def __init__(self, reply):
        self._reply = reply
        self.seen = None

    def complete(self, prompt, system):
        self.seen = (prompt, system)
        return self._reply


_GOOD = (
    '```json\n'
    '{"title": "Marte", "chapters": ['
    '{"title": "Exploración", "sections": ["Insight", "Perseverance"]}'
    ']}\n```'
)


def test_parses_chapters_and_sections_from_json():
    chat = _FakeChat(_GOOD)
    outline = OutlineGenerator(chat).propose("Marte", ["transcript uno"])

    assert outline.title == "Marte"
    assert [c.title for c in outline.chapters] == ["Exploración"]
    assert outline.chapters[0].sections == ["Insight", "Perseverance"]
    assert "transcript uno" in chat.seen[0]   # full transcript went into the prompt


def test_malformed_reply_raises_controlled_error():
    try:
        OutlineGenerator(_FakeChat("not json at all")).propose("Marte", ["x"])
    except CoffeeError as error:
        assert "outline" in str(error).lower()
    else:
        raise AssertionError("a malformed outline must raise CoffeeError")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
