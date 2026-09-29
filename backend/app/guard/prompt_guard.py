"""T044: `GroqPromptGuard` — implementação de `InputGuard` usando o Llama
Prompt Guard 2 86M hospedado na Groq (decisão O2 do plan.md).

Comportamento de falha (constituição, Princípio III — fail-open com
degradação): se o circuito estiver aberto, ou se a chamada falhar/exceder o
timeout, `check` NUNCA lança — retorna `allow` com `source="skipped_degraded"`,
e quem chama (core/pipeline.py) aplica as defesas locais mais restritas.
"""

from __future__ import annotations

from app.core.config import Settings
from app.guard.base import GuardVerdict
from app.guard.circuit_breaker import CircuitBreaker
from app.guard.heuristics import looks_suspicious
from app.observability.logging import get_logger

logger = get_logger(__name__)

# Prompt Guard 2 tem 512 tokens de contexto (research.md D5); o texto é
# truncado defensivamente antes de enviar, mesmo que a validação de tamanho
# do pipeline já limite a 500 caracteres.
_MAX_CHARS_SENT_TO_GUARD = 2000


class GroqPromptGuard:
    def __init__(self, settings: Settings, circuit_breaker: CircuitBreaker) -> None:
        self._settings = settings
        self._circuit_breaker = circuit_breaker
        self._client = None
        if settings.groq_api_key:
            from groq import Groq

            self._client = Groq(
                api_key=settings.groq_api_key, timeout=settings.guard_timeout_seconds
            )

    def check(self, text: str) -> GuardVerdict:
        # Defesa local sempre ativa, mesmo quando o modelo está disponível —
        # é gratuita e pega o caso óbvio antes de gastar uma chamada de API.
        if looks_suspicious(text):
            return GuardVerdict(decision="block", score=1.0, source="local")

        if self._client is None or self._circuit_breaker.is_open():
            return GuardVerdict(decision="allow", score=None, source="skipped_degraded")

        try:
            response = self._client.chat.completions.create(
                model=self._settings.groq_guard_model,
                messages=[{"role": "user", "content": text[:_MAX_CHARS_SENT_TO_GUARD]}],
            )
            self._circuit_breaker.record_success()
            label = response.choices[0].message.content.strip().upper()
            # Convenção do Prompt Guard 2: rótulo positivo indica injection/jailbreak.
            is_malicious = "MALICIOUS" in label or label == "1" or label == "LABEL_1"
            return GuardVerdict(
                decision="block" if is_malicious else "allow",
                score=1.0 if is_malicious else 0.0,
                source="model",
            )
        except Exception:  # noqa: BLE001 — fail-open é intencional
            logger.exception("guard.groq_call_failed")
            self._circuit_breaker.record_failure()
            return GuardVerdict(decision="allow", score=None, source="skipped_degraded")
