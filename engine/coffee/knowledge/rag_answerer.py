"""Answer a question grounded in retrieved passages (RAG generation half).

Given a question, it retrieves the most relevant passages and asks the
``ChatModel`` to answer using ONLY that context, citing episode numbers. If
nothing is retrieved it returns a fixed "I don't know" answer WITHOUT calling
the model — the guardrail that keeps the system from inventing facts the
podcast never covered.
"""

from __future__ import annotations

from dataclasses import dataclass

from coffee.ai.chat_model import ChatModel
from coffee.knowledge.passage import Passage
from coffee.knowledge.passage_retriever import PassageRetriever

_SYSTEM = (
    "Eres un asistente que responde EXCLUSIVAMENTE con la información del "
    "contexto proporcionado, en español. Cita el número de episodio entre "
    "paréntesis cuando uses un dato. Si el contexto no contiene la respuesta, "
    "dilo claramente; nunca inventes."
)

_DONT_KNOW = "No encuentro información sobre eso en los episodios disponibles."


@dataclass(frozen=True)
class RagAnswer:
    """A grounded answer plus the passages it was based on (for citation)."""

    text: str
    sources: list[Passage]


class RagAnswerer:
    """Retrieves context and asks the chat model for a grounded answer."""

    def __init__(self, retriever: PassageRetriever, chat: ChatModel,
                 k: int = 5) -> None:
        self._retriever = retriever
        self._chat = chat
        self._k = k

    def answer(self, question: str) -> RagAnswer:
        passages = self._retriever.retrieve(question, k=self._k)
        if not passages:
            return RagAnswer(_DONT_KNOW, [])
        prompt = self._build_prompt(question, passages)
        text = self._chat.complete(prompt, system=_SYSTEM)
        return RagAnswer(text, passages)

    @staticmethod
    def _build_prompt(question: str, passages: list[Passage]) -> str:
        blocks = [
            f"[Episodio {p.episode} · {p.date} · {p.topic}]\n{p.text}"
            for p in passages
        ]
        context = "\n\n".join(blocks)
        return f"Contexto:\n{context}\n\nPregunta: {question}"
