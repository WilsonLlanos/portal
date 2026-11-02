"""Sanitização dos textos do visitante antes de qualquer registro
(feature 002, FR-008; data-model.md § Sanitização).

E-mails viram `[email]` e sequências com 9 ou mais dígitos (telefone, CPF...)
viram `[número]`. O limite de 9 dígitos preserva anos e intervalos de anos,
como `2019-2024` (8 dígitos), que aparecem em perguntas legítimas.
"""

from __future__ import annotations

import re

from app.llm.base import Message

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# 9+ dígitos, aceitando espaços, pontos, traços e parênteses entre eles.
_LONG_NUMBER_PATTERN = re.compile(r"\+?\d(?:[\s().-]*\d){8,}")


def sanitize_text(text: str) -> str:
    text = _EMAIL_PATTERN.sub("[email]", text.strip())
    return _LONG_NUMBER_PATTERN.sub("[número]", text)


def sanitize_history(history: list[Message]) -> list[dict]:
    # As mensagens do assistente também: a resposta pode repetir um dado
    # digitado pelo visitante.
    return [{"role": turn.role, "content": sanitize_text(turn.content)} for turn in history]
