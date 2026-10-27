"""Write one book section, grounded in retrieved passages (RAG generation half).

Given the book/chapter/section titles, it retrieves the most relevant passages
for the section and asks the chat model for continuous didactic prose in Spanish,
citing episode numbers. With no passages it returns a placeholder and does NOT
call the model (the grounding guardrail).
"""

from __future__ import annotations

from coffee.knowledge.book import WrittenSection

_SYSTEM = (
    "Eres un divulgador científico que redacta en español prosa continua y "
    "didáctica usando EXCLUSIVAMENTE el contexto. Cita el número de episodio "
    "entre paréntesis cuando uses un dato. No inventes."
)

_EMPTY = "_(Sin material suficiente en la selección para esta sección.)_"


class SectionWriter:
    """Retrieves context and writes a grounded section."""

    def __init__(self, chat, k: int = 5) -> None:
        self._chat = chat
        self._k = k

    def write(self, book_title: str, chapter_title: str, section_title: str,
              retriever) -> WrittenSection:
        passages = retriever.retrieve(section_title, k=self._k)
        if not passages:
            return WrittenSection(section_title, _EMPTY, [])
        context = "\n\n".join(
            f"[Episodio {p.episode}] {p.text}" for p in passages
        )
        prompt = (
            f"Libro: {book_title}\nCapítulo: {chapter_title}\n"
            f"Sección: {section_title}\n\nContexto:\n{context}\n\n"
            "Redacta esta sección como prosa continua."
        )
        text = self._chat.complete(prompt, system=_SYSTEM)
        return WrittenSection(section_title, text, passages)
