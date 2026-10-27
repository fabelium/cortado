"""Render a written Book to a single Markdown document (pure, no I/O).

Layout: H1 title, an index of chapters, then each chapter (H2, numbered) with its
sections (H3), the grounded prose and a one-line citation of the episodes used.
"""

from __future__ import annotations

from coffee.knowledge.book import Book, WrittenSection


class MarkdownRenderer:
    """Turns a Book into Markdown text."""

    def render(self, book: Book) -> str:
        lines = [f"# {book.title}", "", "## Índice", ""]
        for number, chapter in enumerate(book.chapters, 1):
            lines.append(f"{number}. {chapter.title}")
        lines.append("")
        for number, chapter in enumerate(book.chapters, 1):
            lines += [f"## {number}. {chapter.title}", ""]
            for section in chapter.sections:
                lines += [f"### {section.title}", "", section.text, ""]
                citation = self._sources_line(section)
                if citation:
                    lines += [citation, ""]
        return "\n".join(lines)

    @staticmethod
    def _sources_line(section: WrittenSection) -> str:
        episodes: list[str] = []
        for passage in section.sources:
            tag = f"ep{passage.episode}"
            if tag not in episodes:
                episodes.append(tag)
        return f"*Fuentes: {', '.join(episodes)}*" if episodes else ""
