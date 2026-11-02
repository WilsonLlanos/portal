"""T051: pipeline do chat, na ordem definida em
specs/001-portfolio-portal/contracts/provider-interfaces.md:

validar tamanho -> teto diário -> rate limit -> InputGuard -> VectorStore.search
-> montar prompt com histórico -> LLMClient.stream, com cada etapa
registrada no trace do Langfuse (feature 002, app/observability/tracing.py).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

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
from app.llm.base import LLMClient, LLMUnavailable, Message, Usage
from app.llm.gemini import GeminiLLMClient
from app.observability.logging import get_logger
from app.observability.tracing import ChatTracer
from app.retrieval.base import VectorStore
from app.retrieval.file_store import FileVectorStore, get_kb_manifest_hash

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
        # Trace de cada pergunta (feature 002); os testes injetam um dublê do SDK.
        self.tracer = ChatTracer(self.settings)


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


def _kb_version() -> str:
    try:
        return get_kb_manifest_hash()
    except Exception:  # noqa: BLE001 — base de conhecimento pode não existir ainda em dev
        return "unknown"


def _cost_cents(usage: Usage | None) -> tuple[float, float]:
    """Custo estimado (entrada, saída) em centavos, para o teto diário e o trace."""
    if usage is None:
        return 0.0, 0.0
    return (
        usage.input_tokens / 1_000_000 * _INPUT_COST_CENTS_PER_MTOK,
        usage.output_tokens / 1_000_000 * _OUTPUT_COST_CENTS_PER_MTOK,
    )


def run_chat_pipeline(
    *,
    message: str,
    lang: str,
    history: list[Message],
    visitor_key: str,
    conversation_id: str | None = None,
    deps: ChatDependencies | None = None,
) -> Iterator[PipelineEvent]:
    deps = deps or ChatDependencies()
    settings = deps.settings

    # 1) Tamanho (FR-018). Rejeitadas aqui, antes do trace (feature 002, FR-001).
    if not message.strip():
        yield PipelineEvent(type="error", error_code="empty_message", error_message="empty")
        return
    if len(message) > settings.max_message_length:
        yield PipelineEvent(type="error", error_code="message_too_long", error_message="too_long")
        return

    # Ciclo de vida do trace (feature 002, research.md R8): em todo caminho,
    # `finish` (local, sem rede) roda ANTES do último evento e `flush` (rede)
    # roda DEPOIS dele, quando o consumidor pede o próximo item. Assim o
    # Langfuse nunca atrasa a resposta. O pipeline passa os textos originais;
    # quem sanitiza é o tracer.
    trace = deps.tracer.start_turn(
        question=message, lang=lang, kb_version=_kb_version(), conversation_id=conversation_id
    )
    full_text = ""
    try:
        # 2) Teto diário (FR-024)
        cost_tracker = get_daily_cost_tracker()
        if cost_tracker.is_paused():
            trace.finish("paused", None)
            yield PipelineEvent(type="error", error_code="chat_paused", error_message="paused")
            trace.flush()
            return

        # 3) Rate limit por visitante (FR-018)
        if not deps.rate_limiter.allow(visitor_key, degraded=deps.guard.is_degraded()):
            trace.finish("rate_limited", None)
            yield PipelineEvent(
                type="error", error_code="rate_limited", error_message="rate_limited"
            )
            trace.flush()
            return

        # 4) InputGuard (FR-017, FR-020)
        verdict = trace.observe_guardrail(lambda: deps.guard.check(message))
        if verdict.decision == "block":
            full_text = _refusal_text(lang)
            yield PipelineEvent(type="token", text=full_text)
            trace.finish("refused", full_text)
            yield PipelineEvent(type="done", outcome="refused", suggestions=["projects", "contact"])
            trace.flush()
            return

        # 5) Recuperação (RAG)
        retrieved = []
        try:
            query_embedding = trace.observe_embedding(lambda: deps.llm.embed([message])[0])
            retrieved = trace.observe_retrieval(
                lambda: deps.vector_store.search(query_embedding, lang=lang, top_k=RETRIEVAL_TOP_K),
                lang=lang,
                top_k=RETRIEVAL_TOP_K,
            )
        except LLMUnavailable:
            logger.exception("pipeline.embed_failed")
        except Exception:  # noqa: BLE001 — base de conhecimento pode não existir ainda em dev
            logger.exception("pipeline.retrieval_failed")

        # 6) Prompt + histórico
        system_prompt = build_system_prompt(lang=lang, author_name=AUTHOR_NAME, retrieved=retrieved)
        messages = [*history, Message(role="user", content=message)]

        # 7) Geração (streaming)
        trace.generation_started(system=system_prompt, history=history, question=message)
        usage: Usage | None = None
        try:
            for chunk in deps.llm.stream(
                system=system_prompt,
                messages=messages,
                temperature=CHAT_TEMPERATURE,
                max_output_tokens=CHAT_MAX_OUTPUT_TOKENS,
            ):
                if chunk.text:
                    if not full_text:
                        trace.generation_first_token()
                    full_text += chunk.text
                    yield PipelineEvent(type="token", text=chunk.text)
                if chunk.usage:
                    usage = chunk.usage
        except LLMUnavailable:
            logger.exception("pipeline.llm_stream_failed")
            trace.generation_finished(full_text, usage, 0.0, 0.0, error=True)
            trace.finish("error", full_text)
            yield PipelineEvent(
                type="error", error_code="unavailable", error_message="llm_unavailable"
            )
            trace.flush()
            return

        input_cost_cents, output_cost_cents = _cost_cents(usage)
        cost_tracker.add_cost(input_cost_cents + output_cost_cents)
        trace.generation_finished(
            full_text, usage, input_cost_cents, output_cost_cents, error=False
        )

        outcome = "no_answer" if not retrieved else "answered"
        trace.finish(outcome, full_text)
        yield PipelineEvent(type="done", outcome=outcome, suggestions=["projects", "cv", "contact"])
        trace.flush()
    except GeneratorExit:
        # O visitante fechou a conexão no meio do streaming. Se o trace já foi
        # encerrado (depois do `done`), `finish` não faz nada. Sem `flush`
        # aqui: o fechamento pode ocorrer em qualquer thread; o exportador em
        # segundo plano do SDK envia o trace em melhor esforço.
        trace.finish("disconnected", full_text)
        raise
