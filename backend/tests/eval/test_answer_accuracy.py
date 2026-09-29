"""T039: valida SC-003 contra questions.jsonl — chamadas reais ao Gemini,
puladas sem GEMINI_API_KEY. Ver tests/eval/README.md.
"""

import json
import os
from pathlib import Path

import pytest

from app.core.pipeline import ChatDependencies, run_chat_pipeline

QUESTIONS_PATH = Path(__file__).parent / "questions.jsonl"

requires_live_credentials = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY não configurada — pulando avaliação com chamadas reais (ver README.md)",
)


def _load_questions() -> list[dict]:
    return [
        json.loads(line)
        for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_once(deps: ChatDependencies, question: str, lang: str) -> tuple[str, str]:
    full_text = ""
    outcome = "unknown"
    for event in run_chat_pipeline(
        message=question,
        lang=lang,
        history=[],
        visitor_key=f"eval:{hash(question)}",
        deps=deps,
    ):
        if event.type == "token":
            full_text += event.text
        elif event.type == "done":
            outcome = event.outcome or outcome
    return full_text, outcome


@requires_live_credentials
def test_answer_accuracy_meets_sc003():
    deps = ChatDependencies()
    questions = _load_questions()

    correct = 0
    no_answer_correct = 0
    no_answer_total = 0

    for item in questions:
        text, outcome = _run_once(deps, item["question"], item["lang"])
        expect_no_answer = item.get("expect_no_answer", False)

        if expect_no_answer:
            no_answer_total += 1
            if outcome == "no_answer":
                no_answer_correct += 1
        else:
            mentions = any(
                term.lower() in text.lower() for term in item.get("must_mention_any", [])
            )
            if mentions:
                correct += 1

    answerable = [q for q in questions if not q.get("expect_no_answer")]
    if answerable:
        accuracy = correct / len(answerable)
        assert accuracy >= 0.95, f"Acurácia {accuracy:.0%} abaixo de 95% (SC-003)"

    if no_answer_total:
        assert no_answer_correct == no_answer_total, (
            "Nem toda pergunta sem resposta foi admitida (SC-003)"
        )
