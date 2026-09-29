"""T045: guarda local de reforço — usada sempre como base, e como única
linha de defesa quando o Prompt Guard 2 (Groq) está degradado.

Não substitui um classificador dedicado (é só heurística de regex), mas
é gratuita, instantânea e reduz o abuso mais óbvio enquanto o guardrail
principal estiver fora.
"""

from __future__ import annotations

import re

# Padrões comuns de tentativa de manipulação, em PT e EN. Deliberadamente
# conservador (poucos falsos positivos) — o Prompt Guard 2 é quem faz o
# trabalho fino quando disponível.
_SUSPICIOUS_PATTERNS = [
    re.compile(r"ignor[ea]\s+(as\s+)?(suas\s+)?instru", re.IGNORECASE),
    re.compile(r"ignore\s+(your\s+)?(previous\s+)?instructions", re.IGNORECASE),
    re.compile(
        r"(revele|mostre|reveal|show)\s+(o\s+|your\s+)?(seu\s+)?(prompt|system prompt)",
        re.IGNORECASE,
    ),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"desconsidere\s+(as\s+)?regras", re.IGNORECASE),
    re.compile(r"act as (?!an? ai assistant)", re.IGNORECASE),
]


def looks_suspicious(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SUSPICIOUS_PATTERNS)
