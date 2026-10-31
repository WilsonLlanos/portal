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


# Padrões extras, usados só quando o Prompt Guard 2 está degradado
# (constituição, Princípio III: "defesas locais mais restritas"). Pegam mais
# variações de manipulação ao custo de alguns falsos positivos — aceitável
# enquanto não há classificador para fazer o trabalho fino.
_STRICT_PATTERNS = [
    re.compile(r"system\s+prompt|prompt\s+(do|de)\s+sistema", re.IGNORECASE),
    re.compile(r"jailbreak|\bDAN\b|developer\s+mode|modo\s+desenvolvedor", re.IGNORECASE),
    re.compile(r"pretend\s+(to\s+be|you\s+are)|finja\s+(ser|que)|role\s*-?\s*play", re.IGNORECASE),
    re.compile(r"(suas|tuas)\s+(instru|regras)|your\s+(instructions|rules)", re.IGNORECASE),
    re.compile(
        r"sem\s+(restri|filtro)|without\s+(restrictions|filters)|no\s+restrictions", re.IGNORECASE
    ),
    re.compile(r"esque[cç]a\s+(tudo|as|o\s+que)|forget\s+(everything|all|your)", re.IGNORECASE),
]


def looks_suspicious(text: str, *, strict: bool = False) -> bool:
    patterns = _SUSPICIOUS_PATTERNS + _STRICT_PATTERNS if strict else _SUSPICIOUS_PATTERNS
    return any(pattern.search(text) for pattern in patterns)
