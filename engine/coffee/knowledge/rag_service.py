"""Compose the knowledge pieces into a chat session over a set of fragments.

``open_session`` runs the read side of RAG end to end: transcribe each selected
fragment (cached), chunk the transcripts into passages, index them, and hand back
a ready ``RagAnswerer``. The caller then asks as many questions as it likes
against that one index — matching the product flow "curate a selection, then chat
about it". Pure orchestration: every collaborator is injected (Facade pattern).
"""

from __future__ import annotations

from coffee.ai.chat_model import ChatModel
from coffee.ai.embedding_provider import EmbeddingProvider
from coffee.domain.models import Fragment
from coffee.knowledge.chunker import PassageChunker
from coffee.knowledge.indexing import build_passage_index
from coffee.knowledge.rag_answerer import RagAnswerer
from coffee.knowledge.transcript_store import TranscriptStore


class RagService:
    """Builds a ``RagAnswerer`` over the transcripts of the given fragments."""

    def __init__(
        self,
        transcript_store: TranscriptStore,
        chunker: PassageChunker,
        embeddings: EmbeddingProvider,
        chat: ChatModel,
        k: int = 5,
    ) -> None:
        self._store = transcript_store
        self._chunker = chunker
        self._embeddings = embeddings
        self._chat = chat
        self._k = k

    def open_session(self, fragments: list[Fragment]) -> RagAnswerer:
        """Transcribe, chunk and index the fragments; return a ready answerer."""
        retriever = build_passage_index(
            fragments, self._store, self._chunker, self._embeddings
        )
        return RagAnswerer(retriever, self._chat, k=self._k)
