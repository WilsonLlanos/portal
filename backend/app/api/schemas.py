"""Esquemas Pydantic da API, espelhando
specs/001-portfolio-portal/contracts/chat-api.openapi.yaml.
"""

import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Memória curta (FR-013a, data-model.md § 3): o histórico é truncado no
# servidor em vez de recusado — uma resposta longa da IA não pode derrubar a
# pergunta seguinte do visitante com 422.
MAX_HISTORY_TURNS = 4
MAX_HISTORY_TURN_CHARS = 1000

Lang = Literal["pt-BR", "en"]
ErrorCode = Literal[
    "empty_message",
    "message_too_long",
    "rate_limited",
    "chat_paused",
    "unavailable",
]
Outcome = Literal["answered", "no_answer", "refused"]
Suggestion = Literal["projects", "cv", "contact"]


class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def _truncate_content(cls, value: str) -> str:
        return value[:MAX_HISTORY_TURN_CHARS]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    lang: Lang
    history: list[HistoryTurn] = Field(default_factory=list)
    # Identificador aleatório da conversa, gerado no navegador (feature 002,
    # FR-017). Só UUID é aceito, para o campo não virar canal de texto livre no
    # painel; outro valor é descartado em silêncio (vira None), sem 422.
    conversation_id: str | None = None

    @field_validator("conversation_id", mode="before")
    @classmethod
    def _keep_only_uuid(cls, value: object) -> str | None:
        try:
            return str(uuid.UUID(str(value)))
        except ValueError:
            return None

    @field_validator("history")
    @classmethod
    def _keep_recent_turns(cls, value: list[HistoryTurn]) -> list[HistoryTurn]:
        return value[-MAX_HISTORY_TURNS:]


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    guard: Literal["normal", "degraded"]
    chat: Literal["active", "paused"]
    kb_version: str
