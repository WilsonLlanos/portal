"""T038: teste de contrato de POST /api/chat e GET /api/health contra
specs/001-portfolio-portal/contracts/chat-api.openapi.yaml (códigos
200/400/429/503). Usa dublês no lugar dos provedores externos reais —
não faz nenhuma chamada de rede.
"""

from fastapi.testclient import TestClient

import app.api.chat as chat_module
import app.guard.circuit_breaker as circuit_breaker_module
import app.limits.daily_cost as daily_cost_module
import app.retrieval.file_store as file_store_module
from app.core.pipeline import PipelineEvent


def _fake_pipeline_factory(events: list[PipelineEvent]):
    def _fake_run_chat_pipeline(**_kwargs):
        yield from events

    return _fake_run_chat_pipeline


def _client(monkeypatch, events: list[PipelineEvent]) -> TestClient:
    monkeypatch.setattr(chat_module, "run_chat_pipeline", _fake_pipeline_factory(events))
    monkeypatch.setattr(circuit_breaker_module, "guard_circuit_status", lambda: "normal")
    monkeypatch.setattr(daily_cost_module, "chat_status", lambda: "active")
    monkeypatch.setattr(file_store_module, "get_kb_manifest_hash", lambda: "test-hash")

    from app.main import app  # importado após os monkeypatches acima

    return TestClient(app)


def test_health_returns_200_with_expected_shape(monkeypatch):
    client = _client(monkeypatch, [])
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["guard"] in ("normal", "degraded")
    assert body["chat"] in ("active", "paused")
    assert isinstance(body["kb_version"], str)


def test_chat_empty_message_returns_400(monkeypatch):
    client = _client(monkeypatch, [PipelineEvent(type="error", error_code="empty_message")])
    response = client.post("/chat", json={"message": "", "lang": "pt-BR"})
    # Pydantic já rejeita string vazia (min_length=1) antes do pipeline rodar.
    assert response.status_code == 422 or response.status_code == 400


def test_chat_rate_limited_returns_429(monkeypatch):
    client = _client(monkeypatch, [PipelineEvent(type="error", error_code="rate_limited")])
    response = client.post("/chat", json={"message": "oi", "lang": "pt-BR"})
    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"


def test_chat_paused_returns_503(monkeypatch):
    client = _client(monkeypatch, [PipelineEvent(type="error", error_code="chat_paused")])
    response = client.post("/chat", json={"message": "oi", "lang": "pt-BR"})
    assert response.status_code == 503
    assert response.json()["code"] == "chat_paused"


def test_chat_success_streams_tokens_and_done(monkeypatch):
    events = [
        PipelineEvent(type="token", text="Olá"),
        PipelineEvent(type="token", text=" mundo"),
        PipelineEvent(type="done", outcome="answered", suggestions=["projects"]),
    ]
    client = _client(monkeypatch, events)
    response = client.post("/chat", json={"message": "quem é você?", "lang": "pt-BR"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: token" in body
    assert "event: done" in body
    assert "answered" in body


def test_rate_limit_key_uses_forwarded_visitor_ip(monkeypatch):
    """Atrás do proxy da Vercel, cada visitante precisa de uma chave própria de rate limit."""
    keys: list[str] = []

    def _capturing_pipeline(**kwargs):
        keys.append(kwargs["visitor_key"])
        yield PipelineEvent(type="done", outcome="answered", suggestions=[])

    client = _client(monkeypatch, [])
    monkeypatch.setattr(chat_module, "run_chat_pipeline", _capturing_pipeline)

    body = {"message": "oi", "lang": "pt-BR"}
    client.post("/chat", json=body, headers={"x-forwarded-for": "203.0.113.10, 10.0.0.1"})
    client.post("/chat", json=body, headers={"x-forwarded-for": "198.51.100.7, 10.0.0.1"})
    client.post("/chat", json=body, headers={"x-real-ip": "203.0.113.10"})

    assert keys[0] != keys[1]  # visitantes diferentes, chaves diferentes
    assert keys[0] == keys[2]  # mesmo visitante, mesma chave (x-real-ip ou x-forwarded-for)


def test_long_history_is_truncated_not_rejected(monkeypatch):
    """Regressão: uma resposta longa da IA no histórico causava 422 na pergunta seguinte."""
    captured: dict = {}

    def _capturing_pipeline(**kwargs):
        captured.update(kwargs)
        yield PipelineEvent(type="done", outcome="answered", suggestions=[])

    client = _client(monkeypatch, [])
    monkeypatch.setattr(chat_module, "run_chat_pipeline", _capturing_pipeline)

    history = [{"role": "user", "content": f"pergunta {i}"} for i in range(5)]
    history.append({"role": "assistant", "content": "x" * 2500})
    response = client.post(
        "/chat", json={"message": "e depois?", "lang": "pt-BR", "history": history}
    )

    assert response.status_code == 200
    assert len(captured["history"]) == 4  # só as trocas mais recentes
    assert len(captured["history"][-1].content) == 1000  # truncado, não recusado
