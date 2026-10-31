"""T051: pipeline do chat, na ordem definida em
specs/001-portfolio-portal/contracts/provider-interfaces.md:

validar tamanho -> teto diário -> rate limit -> InputGuard -> VectorStore.search
-> montar prompt com histórico -> LLMClient.stream -> registrar interação.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal

from app.core.config import Settings, get_settings
from app.core.prompt import (
    CHAT_MAX_OUTPUT_TOKENS,
    CHAT_TEMPERATURE,
    RETRIEVAL_TOP_K,
    build_system_prompt,
)
from app.guard.base import InputGuard
from app.guard.circuit_breaker import guard_circuit_breaker
from app.guard.prompt_guard import GroqPromptGuard
from app.limits.daily_cost import get_daily_cost_tracker
from app.limits.rate_limit import RateLimiter
from app.llm.base import LLMClient, LLMUnavailable, Message
from app.llm.gemini import GeminiLLMClient
from app.observability.langfuse_client import log_chat_interaction
from app.observability.logging import get_logger
from app.retrieval.base import VectorStore
from app.retrieval.file_store import FileVectorStore

logger = get_logger(__name__)

# Preço aproximado do Gemini Flash-Lite pago (research.md D3, a confirmar
# periodicamente): usado só para o teto diário de custo, não para faturamento.
_INPUT_COST_CENTS_PER_MTOK = 25.0
_OUTPUT_COST_CENTS_PER_MTOK = 150.0

EventType = Literal["token", "done", "error"]


@dataclass(frozen=True)
class PipelineEvent:
    type: EventType
    text: str = ""
    outcome: str | None = None
    suggestions: list[str] | None = None
    error_code: str | None = None
    error_message: str | None = None


AUTHOR_NAME = "Wilson Llanos"


class ChatDependencies:
    """Agrupa as implementações concretas das interfaces (T015-T017), para
    facilitar a troca por configuração (constituição, Princípio VI) e o uso
    de dublês (fakes) nos testes.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm: LLMClient = GeminiLLMClient(self.settings)
        self.vector_store: VectorStore = FileVectorStore(self.settings)
        self.guard: InputGuard = GroqPromptGuard(self.settings, guard_circuit_breaker)
        self.rate_limiter = RateLimiter(self.settings)


def _refusal_text(lang: str) -> str:
    if lang == "pt-BR":
        return (
            "Prefiro manter nossa conversa focada na carreira e nos projetos do Wilson. "
            "Pergunte à vontade sobre a experiência dele em IA, ou veja os projetos e o CV dele!"
        )
    return (
        "I'd rather keep our conversation focused on Wilson's career and projects. "
        "Feel free to ask about his AI experience, or check out his projects and CV!"
    )


_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# 8+ dígitos, com espaços, pontos, traços ou parênteses no meio (telefone, CPF...).
_LONG_NUMBER_PATTERN = re.compile(r"\+?\d[\d\s().-]{6,}\d")


def _sanitize_for_log(message: str) -> str:
    """Remove dados pessoais óbvios que o visitante possa ter digitado
    (FR-022): e-mails e números longos viram marcadores."""
    text = _EMAIL_PATTERN.sub("[email]", message.strip())
    text = _LONG_NUMBER_PATTERN.sub("[número]", text)
    return text


def run_chat_pipeline(
    *,
    message: str,
    lang: str,
    history: list[Message],
    visitor_key: str,
    deps: ChatDependencies | None = None,
) -> Iterator[PipelineEvent]:
    deps = deps or ChatDependencies()
    settings = deps.settings
    started_at = time.monotonic()
    sanitized_question = _sanitize_for_log(message)

    def log(**fields: Any) -> None:
        # Toda interação registrada leva a pergunta sanitizada e a latência
        # (constituição, Princípio VIII; FR-021), além dos campos de cada etapa.
        log_chat_interaction(
            question=sanitized_question,
            latency_ms=int((time.monotonic() - started_at) * 1000),
            **fields,
        )

    # 1) Tamanho (FR-018)
    if not message.strip():
        yield PipelineEvent(type="error", error_code="empty_message", error_message="empty")
        return
    if len(message) > settings.max_message_length:
        yield PipelineEvent(type="error", error_code="message_too_long", error_message="too_long")
        return

    # 2) Teto diário (FR-024)
    cost_tracker = get_daily_cost_tracker()
    if cost_tracker.is_paused():
        yield PipelineEvent(type="error", error_code="chat_paused", error_message="paused")
        log(lang=lang, outcome="paused")
        return

    # 3) Rate limit por visitante (FR-018)
    if not deps.rate_limiter.allow(visitor_key, degraded=deps.guard.is_degraded()):
        yield PipelineEvent(type="error", error_code="rate_limited", error_message="rate_limited")
        log(lang=lang, outcome="rate_limited")
        return

    # 4) InputGuard (FR-017, FR-020)
    verdict = deps.guard.check(message)
    if verdict.decision == "block":
        yield PipelineEvent(type="token", text=_refusal_text(lang))
        yield PipelineEvent(type="done", outcome="refused", suggestions=["projects", "contact"])
        log(lang=lang, outcome="refused", guard_result=verdict.source, guard_score=verdict.score)
        return

    # 5) Recuperação (RAG)
    retrieved = []
    try:
        query_embedding = deps.llm.embed([message])[0]
        retrieved = deps.vector_store.search(query_embedding, lang=lang, top_k=RETRIEVAL_TOP_K)
    except LLMUnavailable:
        logger.exception("pipeline.embed_failed")
    except Exception:  # noqa: BLE001 — base de conhecimento pode não existir ainda em dev
        logger.exception("pipeline.retrieval_failed")

    # 6) Prompt + histórico
    system_prompt = build_system_prompt(lang=lang, author_name=AUTHOR_NAME, retrieved=retrieved)
    messages = [*history, Message(role="user", content=message)]

    # 7) Geração (streaming)
    full_text = ""
    input_tokens = 0
    output_tokens = 0
    try:
        for chunk in deps.llm.stream(
            system=system_prompt,
            messages=messages,
            temperature=CHAT_TEMPERATURE,
            max_output_tokens=CHAT_MAX_OUTPUT_TOKENS,
        ):
            if chunk.text:
                full_text += chunk.text
                yield PipelineEvent(type="token", text=chunk.text)
            if chunk.usage:
                input_tokens = chunk.usage.input_tokens
                output_tokens = chunk.usage.output_tokens
    except LLMUnavailable:
        logger.exception("pipeline.llm_stream_failed")
        yield PipelineEvent(type="error", error_code="unavailable", error_message="llm_unavailable")
        log(lang=lang, outcome="error", guard_result=verdict.source)
        return

    cost_cents = (
        input_tokens / 1_000_000 * _INPUT_COST_CENTS_PER_MTOK
        + output_tokens / 1_000_000 * _OUTPUT_COST_CENTS_PER_MTOK
    )
    cost_tracker.add_cost(cost_cents)

    outcome = "no_answer" if not retrieved else "answered"
    suggestions = ["projects", "cv", "contact"]
    yield PipelineEvent(type="done", outcome=outcome, suggestions=suggestions)

    log(
        lang=lang,
        outcome=outcome,
        guard_result=verdict.source,
        retrieved_chunk_ids=[item.chunk.id for item in retrieved],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_estimate_cents=cost_cents,
    )
