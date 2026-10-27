"""SectionWriter: retrieve passages for a section and write grounded prose,
keeping the passages as its sources. Fakes keep it offline.
Run: python3 tests/test_section_writer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.knowledge.passage import Passage
from coffee.knowledge.section_writer import SectionWriter


def _passage(episode=237):
    return Passage("la sonda Insight aterrizó", f"ep{episode}@0-10", episode,
                   "2019-10-17", "Marte", 0)


class _FakeRetriever:
    def __init__(self, passages):
        self._passages = passages
        self.asked = []

    def retrieve(self, question, k):
        self.asked.append((question, k))
        return self._passages


class _FakeChat:
    def __init__(self):
        self.seen = None

    def complete(self, prompt, system):
        self.seen = (prompt, system)
        return "Prosa redactada sobre la llegada (237)."


def test_writes_section_grounded_in_retrieved_passages():
    retriever = _FakeRetriever([_passage(237)])
    chat = _FakeChat()

    section = SectionWriter(chat, k=4).write("Marte", "Exploración", "La llegada", retriever)

    assert section.title == "La llegada"
    assert section.text == "Prosa redactada sobre la llegada (237)."
    assert section.sources == [_passage(237)]
    assert retriever.asked == [("La llegada", 4)]
    assert "Exploración" in chat.seen[0] and "Marte" in chat.seen[0]  # context in prompt


def test_no_passages_yields_a_placeholder_without_calling_the_model():
    chat = _FakeChat()

    section = SectionWriter(chat).write("Marte", "Exploración", "Vacía", _FakeRetriever([]))

    assert section.sources == []
    assert chat.seen is None          # model not called when there is nothing to ground on
    assert section.text               # a non-empty placeholder


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
