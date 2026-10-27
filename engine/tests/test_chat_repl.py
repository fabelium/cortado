"""The human CLI's --chat REPL: format grounded answers and loop over questions.

I/O is injected (read/write) so the loop is tested without a real terminal, and
a fake answerer keeps it free of Gemini/audio. Run: python3 tests/test_chat_repl.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.cli import format_chat_answer, run_chat_repl
from coffee.knowledge.passage import Passage
from coffee.knowledge.rag_answerer import RagAnswer


def _passage(episode=237, topic="Insight en Marte", index=0):
    return Passage(f"texto {index}", f"ep{episode}@0-10", episode,
                   "2019-10-17", topic, index)


def test_format_chat_answer_lists_each_cited_episode_once():
    answer = RagAnswer(
        "Insight aterrizó en Marte en 2018 (237).",
        [_passage(237, index=0), _passage(237, index=1), _passage(305, "Júpiter")],
    )

    text = format_chat_answer(answer)

    assert "Insight aterrizó en Marte en 2018 (237)." in text
    assert text.count("ep237") == 1   # two passages, same episode -> one citation
    assert "ep305" in text


def test_format_chat_answer_without_sources_is_just_the_text():
    text = format_chat_answer(RagAnswer("No encuentro información sobre eso.", []))

    assert text == "No encuentro información sobre eso."  # no "Sources:" line


class _FakeAnswerer:
    def __init__(self):
        self.asked = []

    def answer(self, question):
        self.asked.append(question)
        return RagAnswer(f"respuesta a: {question}", [_passage()])


def test_repl_answers_each_question_until_empty_line():
    answerer = _FakeAnswerer()
    inputs = iter(["¿cuándo aterrizó Insight?", ""])
    written = []

    run_chat_repl(answerer, read=lambda _prompt: next(inputs), write=written.append)

    assert answerer.asked == ["¿cuándo aterrizó Insight?"]  # stopped at empty line
    assert any("respuesta a: ¿cuándo aterrizó Insight?" in line for line in written)


def test_repl_quits_on_exit_without_asking():
    answerer = _FakeAnswerer()
    inputs = iter(["exit", "should not be reached"])

    run_chat_repl(answerer, read=lambda _prompt: next(inputs), write=lambda _m: None)

    assert answerer.asked == []  # 'exit' ends the loop immediately


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
