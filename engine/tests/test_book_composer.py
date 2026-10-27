"""BookComposer: orchestrate transcripts -> outline -> per-section writing into a
Book. Collaborators are doubles. Run: python3 tests/test_book_composer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.knowledge.book import BookOutline, Chapter, WrittenSection
from coffee.knowledge.book_composer import BookComposer


class _FakeStore:
    def get(self, fragment):
        return f"transcript {fragment}"


class _FakeOutline:
    def __init__(self):
        self.seen = None

    def propose(self, title, transcripts):
        self.seen = (title, transcripts)
        return BookOutline("Marte", [Chapter("Exploración", ["La llegada", "El robot"])])


class _FakeWriter:
    def __init__(self):
        self.calls = []

    def write(self, book_title, chapter_title, section_title, retriever):
        self.calls.append((book_title, chapter_title, section_title, retriever))
        return WrittenSection(section_title, f"prosa de {section_title}", [])


def test_composes_book_from_outline_and_written_sections():
    writer = _FakeWriter()
    outline = _FakeOutline()
    composer = BookComposer(_FakeStore(), outline, writer,
                            index_builder=lambda frags: "RETRIEVER")

    book = composer.compose(["f1", "f2"], "Marte")

    assert outline.seen == ("Marte", ["transcript f1", "transcript f2"])
    assert book.title == "Marte"
    assert [c.title for c in book.chapters] == ["Exploración"]
    titles = [s.title for s in book.chapters[0].sections]
    assert titles == ["La llegada", "El robot"]
    # every section was written with full context and the shared retriever
    assert writer.calls[0] == ("Marte", "Exploración", "La llegada", "RETRIEVER")
    assert len(writer.calls) == 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
