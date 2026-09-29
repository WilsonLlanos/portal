"""T052: `POST /chat` (SSE), conforme
specs/001-portfolio-portal/contracts/chat-api.openapi.yaml.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.schemas import ChatRequest
from app.core.pipeline import PipelineEvent, run_chat_pipeline
from app.limits.rate_limit import make_visitor_key
from app.llm.base import Message

router = APIRouter()

# Mensagens cordiais por código de erro (FR-019), com alternativa de
# contato/CV — mantidas em sincronia com frontend/messages/{lang}.json.
_ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "empty_message": {
        "pt-BR": "Escreva sua pergunta para eu poder responder :)",
        "en": "Please write your question so I can answer :)",
    },
    "message_too_long": {
        "pt-BR": "Sua pergunta é longa demais. Tente resumir em até 500 caracteres.",
        "en": "Your question is too long. Please keep it under 500 characters.",
    },
    "rate_limited": {
        "pt-BR": (
            "Você atingiu o limite de perguntas por hora. "
            "Tente novamente mais tarde, ou entre em contato diretamente."
        ),
        "en": (
            "You've reached the hourly question limit. "
            "Please try again later, or reach out directly."
        ),
    },
    "chat_paused": {
        "pt-BR": (
            "O chat atingiu o limite diário de uso e volta a funcionar amanhã. "
            "Enquanto isso, baixe meu CV ou entre em contato."
        ),
        "en": (
            "The chat has reached its daily usage limit and will be back tomorrow. "
            "Meanwhile, download my CV or get in touch."
        ),
    },
    "unavailable": {
        "pt-BR": (
            "O chat está indisponível no momento. "
            "Tente novamente em instantes ou entre em contato diretamente."
        ),
        "en": (
            "The chat is unavailable right now. "
            "Please try again shortly or reach out directly."
        ),
    },
}

_STATUS_BY_ERROR_CODE = {
    "empty_message": 400,
    "message_too_long": 400,
    "rate_limited": 429,
    "chat_paused": 503,
    "unavailable": 503,
}


def _sse_line(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _to_sse(events: Iterator[PipelineEvent], lang: str) -> Iterator[str]:
    for event in events:
        if event.type == "token":
            yield _sse_line("token", {"text": event.text})
        elif event.type == "done":
            yield _sse_line(
                "done", {"outcome": event.outcome, "suggestions": event.suggestions or []}
            )
        elif event.type == "error":
            code = event.error_code or "unavailable"
            message = _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unavailable"]).get(
                lang, _ERROR_MESSAGES["unavailable"]["en"]
            )
            yield _sse_line("error", {"code": code, "message": message})


def _chain(first: PipelineEvent, rest: Iterator[PipelineEvent]) -> Iterator[PipelineEvent]:
    yield first
    yield from rest


@router.post("/chat")
async def post_chat(payload: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    visitor_key = make_visitor_key(client_ip, user_agent)

    history = [Message(role=turn.role, content=turn.content) for turn in payload.history]

    events = run_chat_pipeline(
        message=payload.message,
        lang=payload.lang,
        history=history,
        visitor_key=visitor_key,
    )

    # As validações que falham antes de qualquer streaming (tamanho, teto
    # diário, rate limit, indisponibilidade) viram respostas HTTP com o
    # código de status correto (400/429/503), não um evento SSE dentro de um
    # 200 — o corpo da resposta ainda não começou a ser enviado neste ponto.
    try:
        first_event = next(events)
    except StopIteration:
        return JSONResponse(
            status_code=503,
            content={
                "code": "unavailable",
                "message": _ERROR_MESSAGES["unavailable"][payload.lang],
            },
        )

    if first_event.type == "error":
        code = first_event.error_code or "unavailable"
        status_code = _STATUS_BY_ERROR_CODE.get(code, 503)
        message = _ERROR_MESSAGES.get(code, _ERROR_MESSAGES["unavailable"]).get(
            payload.lang, _ERROR_MESSAGES["unavailable"]["en"]
        )
        return JSONResponse(status_code=status_code, content={"code": code, "message": message})

    return StreamingResponse(
        _to_sse(_chain(first_event, events), payload.lang),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
