"""Esquemas Pydantic da API, espelhando
specs/001-portfolio-portal/contracts/chat-api.openapi.yaml.
"""

from typing import Literal

from pydantic import BaseModel, Field

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
    content: str = Field(max_length=1000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    lang: Lang
    history: list[HistoryTurn] = Field(default_factory=list, max_length=4)


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    guard: Literal["normal", "degraded"]
    chat: Literal["active", "paused"]
    kb_version: str
