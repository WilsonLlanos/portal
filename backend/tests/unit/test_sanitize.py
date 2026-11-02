"""Feature 002, T004: sanitização dos textos do visitante (FR-008)."""

import pytest

from app.llm.base import Message
from app.observability.sanitize import sanitize_history, sanitize_text


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("meu e-mail é joao.silva@x.com", "meu e-mail é [email]"),
        ("ligue +55 (11) 98765-4321", "ligue [número]"),
        ("ligue 98765-4321", "ligue [número]"),
        ("ligue 987654321", "ligue [número]"),
        ("CPF 123.456.789-09", "CPF [número]"),
    ],
)
def test_masks_personal_data(text, expected):
    assert sanitize_text(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "trabalhou entre 2019-2024?",
        "trabalhou (2019 - 2024)?",
        "usa Python 3.12?",
        "o que fez em 2024?",
        "top_k = 5",
    ],
)
def test_preserves_years_and_versions(text):
    assert sanitize_text(text) == text


def test_sanitize_history_masks_both_roles_and_keeps_order():
    history = [
        Message(role="user", content="sou joao@x.com"),
        Message(role="assistant", content="Anotei joao@x.com e 98765-4321"),
        Message(role="user", content="obrigado"),
    ]

    assert sanitize_history(history) == [
        {"role": "user", "content": "sou [email]"},
        {"role": "assistant", "content": "Anotei [email] e [número]"},
        {"role": "user", "content": "obrigado"},
    ]
