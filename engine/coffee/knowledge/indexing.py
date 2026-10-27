"""Build a passage index over a set of fragments (shared RAG/book pipeline).

Transcribe each fragment (cached by the store), chunk the transcripts into
passages and index them for cosine retrieval. Shared by the chat (RagService)
and the book (BookComposer) so the read-side pipeline lives in one place.
"""

from __future__ import annotations

from coffee.knowledge.passage_retriever import PassageRetriever


def build_passage_index(fragments, store, chunker, embeddings) -> PassageRetriever:
    """Transcribe -> chunk -> index the fragments; return a ready retriever."""
    passages = []
    for fragment in fragments:
        passages.extend(chunker.chunk(fragment, store.get(fragment)))
    retriever = PassageRetriever(embeddings)
    retriever.index(passages)
    return retriever
