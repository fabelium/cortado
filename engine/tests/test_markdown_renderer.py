"""MarkdownRenderer: a composed Book renders to one Markdown document with an
index, numbered chapters, section headings, prose and a per-section source line.
Pure (no LLM). Run: python3 tests/test_markdown_renderer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.knowledge.book import Book, WrittenChapter, WrittenSection
from coffee.knowledge.markdown_renderer import MarkdownRenderer
from coffee.knowledge.passage import Passage


def _passage(episode=237):
    return Passage("texto", f"ep{episode}@0-10", episode, "2019-10-17", "Marte", 0)


def _book():
    section = WrittenSection("La llegada", "Insight aterrizó en Marte (237).",
                             [_passage(237), _passage(237), _passage(305)])
    chapter = WrittenChapter("Exploración de Marte", [section])
    return Book("Marte", [chapter])


def test_render_has_title_index_and_chapter_heading():
    md = MarkdownRenderer().render(_book())
    assert md.startswith("# Marte")
    assert "## Índice" in md
    assert "1. Exploración de Marte" in md      # index entry
    assert "## 1. Exploración de Marte" in md   # chapter heading
    assert "### La llegada" in md               # section heading
    assert "Insight aterrizó en Marte (237)." in md


def test_render_lists_each_source_episode_once():
    md = MarkdownRenderer().render(_book())
    assert "Fuentes: ep237, ep305" in md   # deduped, first-seen order
    assert md.count("ep237") == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
