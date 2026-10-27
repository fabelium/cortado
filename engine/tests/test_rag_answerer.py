"""RagAnswerer: answer a question grounded in retrieved passages, citing
episodes, with an "I don't know" guardrail when nothing is retrieved. Written
test-first with fake retriever + chat (no embeddings, no API).
Run: python3 tests/test_rag_answerer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.knowledge.passage import Passage
from coffee.knowledge.rag_answerer import RagAnswerer


class FakeChat:
    """Records prompts; returns a canned answer (or echoes the prompt)."""

    def __init__(self, response="una respuesta", echo=False):
        self._response = response
        self._echo = echo
        self.calls = []
        self.model_id = "fake"

    def complete(self, prompt, *, system=None):
        self.calls.append((prompt, system))
        return prompt if self._echo else self._response


class FakeRetriever:
    def __init__(self, passages):
        self._passages = passages

    def retrieve(self, query, k=5):
        return self._passages[:k]


def _passage(text, episode=256):
    return Passage(text=text, fragment_id=f"ep{episode}@0-60", episode=episode,
                   date="2020-02-27", topic="materia oscura", index=0)


def test_no_passages_says_dont_know_and_skips_model():
    chat = FakeChat()
    answerer = RagAnswerer(FakeRetriever([]), chat)
    result = answerer.answer("¿qué es la materia oscura?")
    assert result.sources == []
    assert "no encuentro" in result.text.lower()  # guardrail message
    assert chat.calls == []                        # model never called


def test_grounds_prompt_with_passages_and_citations():
    passages = [_passage("La materia oscura no emite luz.", episode=256)]
    chat = FakeChat(echo=True)
    answerer = RagAnswerer(FakeRetriever(passages), chat)
    answerer.answer("¿qué es la materia oscura?")
    prompt = chat.calls[0][0]
    assert "La materia oscura no emite luz." in prompt  # passage text in context
    assert "256" in prompt                              # episode citation available


def test_returns_model_answer_and_sources():
    passages = [_passage("contexto relevante")]
    chat = FakeChat(response="La materia oscura es masa invisible.")
    answerer = RagAnswerer(FakeRetriever(passages), chat)
    result = answerer.answer("¿qué es la materia oscura?")
    assert result.text == "La materia oscura es masa invisible."
    assert result.sources == passages


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
