"""Value objects for the book-style summary (frozen, pure data).

An outline is the proposed structure (chapter and section titles); a Book is the
same structure once every section has been written, each carrying the passages
it was grounded in for citation.
"""

from __future__ import annotations

from dataclasses import dataclass

from coffee.knowledge.passage import Passage


@dataclass(frozen=True)
class Chapter:
    """A proposed chapter: a title and its section titles."""

    title: str
    sections: list[str]


@dataclass(frozen=True)
class BookOutline:
    """The proposed didactic structure for the whole book."""

    title: str
    chapters: list[Chapter]


@dataclass(frozen=True)
class WrittenSection:
    """A written section: grounded prose plus the passages it cites."""

    title: str
    text: str
    sources: list[Passage]


@dataclass(frozen=True)
class WrittenChapter:
    """A chapter whose sections have been written."""

    title: str
    sections: list[WrittenSection]


@dataclass(frozen=True)
class Book:
    """A fully written book, ready to render."""

    title: str
    chapters: list[WrittenChapter]
