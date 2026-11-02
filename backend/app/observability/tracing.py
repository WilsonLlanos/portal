"""Feature 002: trace de cada pergunta do chat no Langfuse (research.md R1, R7, R8;
contracts/trace-structure.md).

O pipeline só conversa com esta fachada (`ChatTracer` -> `ChatTurnTrace`), no
mesmo padrão de `LLMClient`/`VectorStore`/`InputGuard` (constituição,
Princípio VI): ele não importa o SDK do Langfuse nem sanitiza textos.

Por que não há contexto implícito (`@observe`, `start_as_current_observation`):
`run_chat_pipeline` é um gerador, e o FastAPI itera cada pedaço dele numa
thread diferente. Um contexto OpenTelemetry aberto antes de um `yield` e
fechado depois estaria em outro contexto e quebraria. Por isso cada
observação é criada de forma explícita, ligada ao pai pela referência Python.

Por que encerrar (`finish`) e enviar (`flush`) são métodos separados: o
`finish` não usa rede e roda antes do último evento enviado ao visitante; o
`flush` usa rede e roda depois dele, para nunca atrasar a resposta (FR-009).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar

from langfuse import propagate_attributes

from app.core.config import Settings
from app.core.prompt import CHAT_MAX_OUTPUT_TOKENS, CHAT_TEMPERATURE
from app.guard.base import GuardVerdict
from app.llm.base import Message, Usage
from app.observability.langfuse_client import get_langfuse_client
from app.observability.logging import get_logger
from app.observability.sanitize import sanitize_history, sanitize_text
from app.retrieval.base import ScoredChunk

logger = get_logger(__name__)

T = TypeVar("T")


class ChatTurnTrace(Protocol):
    """Uma pergunta do visitante, do início ao fim. Recebe os textos
    originais; quem sanitiza é a implementação, antes de gravar (R7)."""

    is_finished: bool

    def observe_guardrail(self, fn: Callable[[], GuardVerdict]) -> GuardVerdict: ...

    def observe_embedding(self, fn: Callable[[], T]) -> T: ...

    def observe_retrieval(
        self, fn: Callable[[], list[ScoredChunk]], lang: str, top_k: int
    ) -> list[ScoredChunk]: ...

    def generation_started(self, system: str, history: list[Message], question: str) -> None: ...

    def generation_first_token(self) -> None: ...

    def generation_finished(
        self,
        output: str,
        usage: Usage | None,
        input_cost_cents: float,
        output_cost_cents: float,
        error: bool,
    ) -> None: ...

    def finish(self, outcome: str, answer: str | None) -> None:
        """Encerra a raiz localmente, sem rede. A segunda chamada não faz nada."""
        ...

    def flush(self) -> None:
        """Envia os dados. É o único método com rede."""
        ...


class NoopChatTurnTrace:
    """Usado sem as chaves do Langfuse (dev e CI): só emite o log JSON
    `chat.interaction` no `finish`, para não perder a observabilidade."""

    def __init__(self, question: str, lang: str) -> None:
        self.is_finished = False
        self._started_at = time.monotonic()
        self._fields: dict[str, Any] = {"question": sanitize_text(question), "lang": lang}

    def observe_guardrail(self, fn: Callable[[], GuardVerdict]) -> GuardVerdict:
        verdict = fn()
        self._fields["guard_result"] = verdict.source
        self._fields["guard_score"] = verdict.score
        return verdict

    def observe_embedding(self, fn: Callable[[], T]) -> T:
        return fn()

    def observe_retrieval(
        self, fn: Callable[[], list[ScoredChunk]], lang: str, top_k: int
    ) -> list[ScoredChunk]:
        retrieved = fn()
        self._fields["retrieved_chunk_ids"] = [item.chunk.id for item in retrieved]
        return retrieved

    def generation_started(self, system: str, history: list[Message], question: str) -> None:
        pass

    def generation_first_token(self) -> None:
        pass

    def generation_finished(
        self,
        output: str,
        usage: Usage | None,
        input_cost_cents: float,
        output_cost_cents: float,
        error: bool,
    ) -> None:
        if usage:
            self._fields["input_tokens"] = usage.input_tokens
            self._fields["output_tokens"] = usage.output_tokens
        self._fields["cost_estimate_cents"] = input_cost_cents + output_cost_cents

    def finish(self, outcome: str, answer: str | None) -> None:
        if self.is_finished:
            return
        self.is_finished = True
        latency_ms = int((time.monotonic() - self._started_at) * 1000)
        logger.info(
            "chat.interaction", extra={**self._fields, "outcome": outcome, "latency_ms": latency_ms}
        )

    def flush(self) -> None:
        pass


class LangfuseChatTurnTrace:
    """Trace `chat-turn` com as etapas guardrail -> embed-question ->
    retrieval -> answer. Toda chamada ao SDK passa por `_safe`: uma falha do
    Langfuse vira só um log `observability.trace_failed`, nunca uma exceção
    para o pipeline (FR-009)."""

    def __init__(
        self,
        client: Any,
        settings: Settings,
        question: str,
        lang: str,
        kb_version: str,
        conversation_id: str | None,
    ) -> None:
        self.is_finished = False
        self._client = client
        self._settings = settings
        self._started_at = time.monotonic()
        self._question = sanitize_text(question)
        self._attributes = {
            "session_id": conversation_id,
            "trace_name": "chat-turn",
            "metadata": {"lang": lang, "kb_version": kb_version},
        }
        self._generation: Any = None
        self._first_token_at: datetime | None = None
        self._root = self._safe(
            lambda: self._create(
                client.start_observation, name="chat-turn", as_type="span", input=self._question
            )
        )

    def _safe(self, fn: Callable[[], T]) -> T | None:
        try:
            return fn()
        except Exception:  # noqa: BLE001 — a observabilidade nunca derruba o chat
            logger.exception("observability.trace_failed")
            return None

    def _create(self, factory: Callable[..., Any], **kwargs: Any) -> Any:
        # Bloco curto, sem `yield` dentro: aplica sessão, nome, idioma e versão
        # da base a cada observação criada (R2).
        with propagate_attributes(**self._attributes):
            return factory(**kwargs)

    def _child(self, **kwargs: Any) -> Any:
        if self._root is None:
            return None
        return self._safe(lambda: self._create(self._root.start_observation, **kwargs))

    def _end(self, observation: Any, **update: Any) -> None:
        if observation is None:
            return
        fields = {key: value for key, value in update.items() if value is not None}
        self._safe(lambda: observation.update(**fields).end())

    def _run_step(self, observation: Any, fn: Callable[[], T], describe: Callable[[T], dict]) -> T:
        # Exceções de `fn` são repassadas ao pipeline, que já sabe tratá-las.
        try:
            result = fn()
        except Exception as exc:
            self._end(observation, level="ERROR", status_message=str(exc))
            raise
        self._end(observation, **describe(result))
        return result

    def observe_guardrail(self, fn: Callable[[], GuardVerdict]) -> GuardVerdict:
        observation = self._child(name="guardrail", as_type="guardrail", input=self._question)
        return self._run_step(
            observation,
            fn,
            lambda verdict: {
                "output": {
                    "decision": verdict.decision,
                    "score": verdict.score,
                    "source": verdict.source,
                },
                "level": "WARNING" if verdict.source == "skipped_degraded" else None,
            },
        )

    def observe_embedding(self, fn: Callable[[], T]) -> T:
        observation = self._child(
            name="embed-question",
            as_type="embedding",
            model=self._settings.gemini_embedding_model,
            input=self._question,
        )
        return self._run_step(observation, fn, lambda _result: {})

    def observe_retrieval(
        self, fn: Callable[[], list[ScoredChunk]], lang: str, top_k: int
    ) -> list[ScoredChunk]:
        observation = self._child(
            name="retrieval", as_type="retriever", input={"lang": lang, "top_k": top_k}
        )

        def describe(retrieved: list[ScoredChunk]) -> dict:
            if not retrieved:
                return {"output": []}
            top_score = max(item.score for item in retrieved)
            if self._root is not None:
                self._safe(
                    lambda: self._root.score_trace(
                        name="retrieval_top_score", value=top_score, data_type="NUMERIC"
                    )
                )
            return {
                "output": [{"id": item.chunk.id, "score": item.score} for item in retrieved],
                "metadata": {"top_score": top_score},
            }

        return self._run_step(observation, fn, describe)

    def generation_started(self, system: str, history: list[Message], question: str) -> None:
        self._generation = self._child(
            name="answer",
            as_type="generation",
            model=self._settings.gemini_model,
            model_parameters={
                "temperature": CHAT_TEMPERATURE,
                "max_output_tokens": CHAT_MAX_OUTPUT_TOKENS,
            },
            input=[
                {"role": "system", "content": system},
                *sanitize_history(history),
                {"role": "user", "content": sanitize_text(question)},
            ],
        )

    def generation_first_token(self) -> None:
        # Só guarda o instante; o envio acontece no fim da geração.
        self._first_token_at = datetime.now(UTC)

    def generation_finished(
        self,
        output: str,
        usage: Usage | None,
        input_cost_cents: float,
        output_cost_cents: float,
        error: bool,
    ) -> None:
        cost_details = None
        usage_details = None
        if usage:
            usage_details = {"input": usage.input_tokens, "output": usage.output_tokens}
            # O Langfuse espera dólares; o pipeline calcula em centavos.
            cost_details = {
                "input": input_cost_cents / 100,
                "output": output_cost_cents / 100,
                "total": (input_cost_cents + output_cost_cents) / 100,
            }
        self._end(
            self._generation,
            output=sanitize_text(output),
            completion_start_time=self._first_token_at,
            usage_details=usage_details,
            cost_details=cost_details,
            level="ERROR" if error else None,
            status_message="llm_unavailable" if error else None,
        )
        self._generation = None

    def finish(self, outcome: str, answer: str | None) -> None:
        if self.is_finished:
            return
        self.is_finished = True
        sanitized_answer = sanitize_text(answer) if answer is not None else None
        level = {"error": "ERROR", "disconnected": "WARNING"}.get(outcome)

        # Geração interrompida pela desconexão do visitante: fecha com o texto parcial.
        if self._generation is not None:
            self._end(self._generation, output=sanitized_answer, level=level)
            self._generation = None

        root = self._root
        if root is None:
            return
        fields = {
            "output": sanitized_answer,
            "metadata": {
                "outcome": outcome,
                "environment": self._settings.langfuse_tracing_environment,
                "latency_ms": int((time.monotonic() - self._started_at) * 1000),
            },
            "level": level,
        }
        self._safe(lambda: root.update(**{k: v for k, v in fields.items() if v is not None}))
        # Antes do `end`: depois dele a observação não aceita mais dados.
        self._safe(lambda: root.set_trace_io(input=self._question, output=sanitized_answer))
        self._safe(root.end)

    def flush(self) -> None:
        self._safe(lambda: self._client.flush())


class ChatTracer:
    """Abre um `ChatTurnTrace` por pergunta: Langfuse quando o cliente está
    configurado, Noop caso contrário. Os testes injetam um dublê do SDK em
    `client_factory`."""

    def __init__(
        self,
        settings: Settings,
        client_factory: Callable[[], Any] = get_langfuse_client,
    ) -> None:
        self._settings = settings
        self._client_factory = client_factory

    def start_turn(
        self, question: str, lang: str, kb_version: str, conversation_id: str | None
    ) -> ChatTurnTrace:
        client = self._client_factory()
        if client is None:
            return NoopChatTurnTrace(question, lang)
        return LangfuseChatTurnTrace(
            client, self._settings, question, lang, kb_version, conversation_id
        )
