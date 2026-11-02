"""Feature 002, T008: estrutura do trace por outcome, tolerância a falha,
ciclo de vida (research.md R8) e auditoria de privacidade (SC-002).

Usa um dublê do cliente Langfuse que grava cada chamada, e dublês de LLM,
busca, guardrail e rate limit — nenhuma chamada de rede.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import app.core.pipeline as pipeline_module
import app.observability.tracing as tracing_module
from app.core.config import Settings
from app.core.pipeline import run_chat_pipeline
from app.guard.base import GuardVerdict
from app.llm.base import LLMChunk, LLMUnavailable, Message, Usage
from app.observability.tracing import ChatTracer
from app.retrieval.base import ScoredChunk
from app.retrieval.models import KnowledgeChunk

CONVERSATION_ID = "0b7e7c1e-8a4f-4d2b-9f3e-2a6c1d5e4f70"


# --- Dublê do SDK do Langfuse ---------------------------------------------------


class FakeObservation:
    def __init__(self, client: FakeLangfuse, name: str, kwargs: dict) -> None:
        self.client = client
        self.name = name
        self.created = kwargs
        self.updates: dict = {}
        self.ended = False
        self.trace_io: dict | None = None
        self.scores: list[dict] = []
        self.attributes = client.current_attributes

    def start_observation(self, **kwargs):
        return self.client._new(kwargs)

    def update(self, **kwargs):
        self.client.calls.append(("update", self.name))
        self.updates.update(kwargs)
        return self

    def end(self):
        self.client.calls.append(("end", self.name))
        self.ended = True
        return self

    def set_trace_io(self, **kwargs):
        self.trace_io = kwargs
        return self

    def score_trace(self, **kwargs):
        self.scores.append(kwargs)

    def field(self, key):
        return self.updates.get(key, self.created.get(key))


class FakeLangfuse:
    def __init__(self) -> None:
        self.observations: list[FakeObservation] = []
        self.calls: list[tuple] = []
        self.current_attributes: dict | None = None

    def _new(self, kwargs: dict) -> FakeObservation:
        observation = FakeObservation(self, kwargs["name"], kwargs)
        self.observations.append(observation)
        self.calls.append(("start", kwargs["name"]))
        return observation

    def start_observation(self, **kwargs):
        return self._new(kwargs)

    def flush(self):
        self.calls.append(("flush",))

    @property
    def names(self) -> list[str]:
        return [observation.name for observation in self.observations]

    def get(self, name: str) -> FakeObservation:
        return next(o for o in self.observations if o.name == name)

    @property
    def flushed(self) -> bool:
        return ("flush",) in self.calls


class ExplodingLangfuse:
    """Cliente que lança exceção em toda chamada."""

    def __getattr__(self, _name):
        raise RuntimeError("langfuse fora do ar")


# --- Dublês do pipeline -----------------------------------------------------------


def _chunk(chunk_id: str, score: float) -> ScoredChunk:
    return ScoredChunk(
        chunk=KnowledgeChunk(id=chunk_id, lang="pt-BR", source="cv", source_id="cv", text="x"),
        score=score,
    )


class FakeLLM:
    def __init__(self, texts=("Olá", " mundo"), fail_after: int | None = None, echo=False):
        self.texts = texts
        self.fail_after = fail_after
        self.echo = echo

    def embed(self, texts):
        return [[0.1, 0.2]]

    def stream(self, *, system, messages, temperature, max_output_tokens):
        texts = self.texts
        if self.echo:
            texts = [f"Anotei seu contato: {messages[-1].content}"]
        for index, text in enumerate(texts):
            if self.fail_after is not None and index >= self.fail_after:
                raise LLMUnavailable("boom")
            yield LLMChunk(text=text)
        if self.fail_after is not None:
            raise LLMUnavailable("boom")
        yield LLMChunk(text="", usage=Usage(input_tokens=1000, output_tokens=200))


class FakeCostTracker:
    def __init__(self, paused=False):
        self.paused = paused

    def is_paused(self):
        return self.paused

    def add_cost(self, cents):
        pass


def _deps(
    client,
    *,
    llm=None,
    retrieved=None,
    verdict=None,
    allow=True,
    environment="production",
):
    settings = Settings(_env_file=None, langfuse_tracing_environment=environment)
    guard = SimpleNamespace(
        check=lambda _text: verdict or GuardVerdict(decision="allow", score=0.01, source="model"),
        is_degraded=lambda: False,
    )
    return SimpleNamespace(
        settings=settings,
        llm=llm or FakeLLM(),
        vector_store=SimpleNamespace(
            search=lambda *_a, **_k: (
                retrieved if retrieved is not None else [_chunk("a", 0.8), _chunk("b", 0.6)]
            )
        ),
        guard=guard,
        rate_limiter=SimpleNamespace(allow=lambda _key, degraded: allow),
        tracer=ChatTracer(settings, client_factory=lambda: client),
    )


@pytest.fixture(autouse=True)
def _patch_environment(monkeypatch):
    @contextmanager
    def fake_propagate(**attributes):
        # Grava os atributos ativos enquanto a observação é criada.
        client = attributes_owner["client"]
        if client is not None:
            client.current_attributes = attributes
        yield
        if client is not None:
            client.current_attributes = None

    attributes_owner: dict = {"client": None}
    monkeypatch.setattr(tracing_module, "propagate_attributes", fake_propagate)
    monkeypatch.setattr(pipeline_module, "get_kb_manifest_hash", lambda: "kb-hash")
    monkeypatch.setattr(pipeline_module, "get_daily_cost_tracker", lambda: FakeCostTracker())
    return attributes_owner


def _run(client, owner=None, *, message="Qual banco vetorial o chat usa?", history=None, **kw):
    if owner is not None and isinstance(client, FakeLangfuse):
        owner["client"] = client
    conversation_id = kw.pop("conversation_id", None)
    return run_chat_pipeline(
        message=message,
        lang="pt-BR",
        history=history or [],
        visitor_key="visitor-hash",
        conversation_id=conversation_id,
        deps=_deps(client, **kw),
    )


# --- Etapas por outcome -----------------------------------------------------------


def test_answered_has_all_steps_and_outcome(_patch_environment):
    client = FakeLangfuse()
    events = list(_run(client, _patch_environment))

    assert [e.type for e in events] == ["token", "token", "done"]
    assert client.names == ["chat-turn", "guardrail", "embed-question", "retrieval", "answer"]
    assert [o.created["as_type"] for o in client.observations] == [
        "span",
        "guardrail",
        "embedding",
        "retriever",
        "generation",
    ]
    root = client.get("chat-turn")
    assert root.updates["metadata"]["outcome"] == "answered"
    assert root.ended and all(o.ended for o in client.observations)
    assert root.scores == [{"name": "retrieval_top_score", "value": 0.8, "data_type": "NUMERIC"}]
    answer = client.get("answer")
    assert answer.field("output") == "Olá mundo"
    assert answer.field("usage_details") == {"input": 1000, "output": 200}
    assert answer.field("completion_start_time") is not None


def test_refused_has_only_guardrail(_patch_environment):
    client = FakeLangfuse()
    verdict = GuardVerdict(decision="block", score=0.99, source="model")
    list(_run(client, _patch_environment, verdict=verdict))

    assert client.names == ["chat-turn", "guardrail"]
    assert client.get("chat-turn").updates["metadata"]["outcome"] == "refused"


def test_rate_limited_has_only_root(_patch_environment):
    client = FakeLangfuse()
    list(_run(client, _patch_environment, allow=False))

    assert client.names == ["chat-turn"]
    root = client.get("chat-turn")
    assert root.updates["metadata"]["outcome"] == "rate_limited"
    assert "output" not in root.updates


def test_paused_has_only_root(_patch_environment, monkeypatch):
    monkeypatch.setattr(pipeline_module, "get_daily_cost_tracker", lambda: FakeCostTracker(True))
    client = FakeLangfuse()
    list(_run(client, _patch_environment))

    assert client.names == ["chat-turn"]
    assert client.get("chat-turn").updates["metadata"]["outcome"] == "paused"


def test_error_marks_answer_with_partial_output(_patch_environment):
    client = FakeLangfuse()
    events = list(_run(client, _patch_environment, llm=FakeLLM(fail_after=1)))

    assert [e.type for e in events] == ["token", "error"]
    answer = client.get("answer")
    assert answer.updates["level"] == "ERROR"
    assert answer.updates["output"] == "Olá"
    root = client.get("chat-turn")
    assert root.updates["metadata"]["outcome"] == "error"
    assert root.updates["level"] == "ERROR"


# --- Campos -------------------------------------------------------------------------


def test_empty_retrieval_has_no_top_score(_patch_environment):
    client = FakeLangfuse()
    list(_run(client, _patch_environment, retrieved=[]))

    assert client.get("retrieval").updates["output"] == []
    assert client.get("chat-turn").scores == []
    assert client.get("chat-turn").updates["metadata"]["outcome"] == "no_answer"


def test_session_only_with_valid_conversation_id(_patch_environment):
    client = FakeLangfuse()
    list(_run(client, _patch_environment, conversation_id=CONVERSATION_ID))
    assert all(o.attributes["session_id"] == CONVERSATION_ID for o in client.observations)
    assert client.get("chat-turn").attributes["metadata"] == {
        "lang": "pt-BR",
        "kb_version": "kb-hash",
    }

    client = FakeLangfuse()
    list(_run(client, _patch_environment))
    assert all(o.attributes["session_id"] is None for o in client.observations)


def test_root_metadata_has_environment(_patch_environment):
    client = FakeLangfuse()
    list(_run(client, _patch_environment, environment="development"))

    assert client.get("chat-turn").updates["metadata"]["environment"] == "development"


def test_guardrail_output_is_verdict(_patch_environment):
    client = FakeLangfuse()
    list(_run(client, _patch_environment))

    assert client.get("guardrail").updates["output"] == {
        "decision": "allow",
        "score": 0.01,
        "source": "model",
    }


# --- Escopo e tolerância a falha ---------------------------------------------------


@pytest.mark.parametrize("message", ["   ", "x" * 501])
def test_invalid_size_creates_no_trace(_patch_environment, message):
    client = FakeLangfuse()
    events = list(_run(client, _patch_environment, message=message))

    assert events[0].type == "error"
    assert client.observations == []


def test_exploding_client_does_not_break_chat():
    events = list(_run(ExplodingLangfuse()))

    assert [e.type for e in events] == ["token", "token", "done"]
    assert events[-1].outcome == "answered"


# --- Ciclo de vida (R8) -----------------------------------------------------------


def test_finish_before_done_and_flush_only_after_it(_patch_environment):
    client = FakeLangfuse()
    events = _run(client, _patch_environment)

    assert next(events).type == "token"
    assert not client.flushed
    assert next(events).type == "token"
    done = next(events)
    assert done.type == "done"
    assert client.get("chat-turn").ended  # encerrado antes de o done ser entregue
    assert not client.flushed

    with pytest.raises(StopIteration):
        next(events)
    assert client.flushed


@pytest.mark.parametrize(
    ("kwargs", "paused", "outcome"),
    [
        ({}, True, "paused"),
        ({"allow": False}, False, "rate_limited"),
        ({"llm": FakeLLM(fail_after=0)}, False, "error"),
    ],
)
def test_first_event_error_path_like_chat_route(
    _patch_environment, monkeypatch, kwargs, paused, outcome
):
    monkeypatch.setattr(pipeline_module, "get_daily_cost_tracker", lambda: FakeCostTracker(paused))
    client = FakeLangfuse()
    events = _run(client, _patch_environment, **kwargs)

    # Como o chat.py: lê só o primeiro evento e devolve o 429/503.
    assert next(events).type == "error"
    root = client.get("chat-turn")
    assert root.ended
    assert root.updates["metadata"]["outcome"] == outcome
    assert not client.flushed

    # A BackgroundTask consome o resto do gerador.
    list(events)
    assert client.flushed


def test_close_mid_stream_marks_disconnected(_patch_environment):
    client = FakeLangfuse()
    events = _run(client, _patch_environment)
    next(events)
    events.close()

    root = client.get("chat-turn")
    assert root.updates["metadata"]["outcome"] == "disconnected"
    assert root.updates["level"] == "WARNING"
    assert root.updates["output"] == "Olá"
    assert client.get("answer").ended
    assert not client.flushed


def test_close_after_done_keeps_outcome(_patch_environment):
    client = FakeLangfuse()
    events = _run(client, _patch_environment)
    for event in events:
        if event.type == "done":
            break
    events.close()

    assert client.get("chat-turn").updates["metadata"]["outcome"] == "answered"


# --- Auditoria de privacidade (SC-002) -------------------------------------------


@pytest.mark.parametrize("index", range(50))
def test_privacy_audit(_patch_environment, index):
    email = f"pessoa{index}@exemplo{index}.com"
    phone = f"+55 11 9{index:04d}-{index:04d}"
    client = FakeLangfuse()
    history = [
        Message(role="user", content=f"meu telefone é {phone}"),
        Message(role="assistant", content=f"Anotei {email}"),
    ]
    list(
        _run(
            client,
            _patch_environment,
            message=f"Pode responder em {email} ou {phone}?",
            history=history,
            llm=FakeLLM(echo=True),
        )
    )

    payloads = []
    for observation in client.observations:
        payloads += [observation.created, observation.updates, observation.trace_io]
    dumped = json.dumps(payloads, default=str, ensure_ascii=False)

    assert email not in dumped
    assert phone not in dumped
    assert phone.replace(" ", "") not in dumped
    assert "visitor-hash" not in dumped
    assert client.get("answer").updates["output"].count("[email]") == 1
    assert "[email]" in client.get("chat-turn").trace_io["output"]
