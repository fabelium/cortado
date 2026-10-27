"""Compose a Book from a curated selection (Facade over the book pieces).

Reads the full transcripts to propose a global outline, builds a passage index
for retrieval, writes each section grounded in that index and assembles a Book.
Every collaborator is injected; the index builder is a callable so wiring lives
in the composition root.
"""

from __future__ import annotations

from coffee.knowledge.book import Book, WrittenChapter


class BookComposer:
    """Orchestrates outline + section writing into a finished Book."""

    def __init__(self, store, outline_generator, section_writer, index_builder) -> None:
        self._store = store
        self._outline = outline_generator
        self._writer = section_writer
        self._index_builder = index_builder

    def compose(self, fragments, title: str) -> Book:
        transcripts = [self._store.get(fragment) for fragment in fragments]
        outline = self._outline.propose(title, transcripts)
        retriever = self._index_builder(fragments)
        chapters = []
        for chapter in outline.chapters:
            sections = [
                self._writer.write(outline.title, chapter.title, section, retriever)
                for section in chapter.sections
            ]
            chapters.append(WrittenChapter(chapter.title, sections))
        return Book(outline.title, chapters)
