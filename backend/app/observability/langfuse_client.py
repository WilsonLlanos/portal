"""T022: cliente Langfuse tolerante a falha (FR-021/FR-022).

Se as chaves não estiverem configuradas, ou se o Langfuse estiver fora do
ar, o registro é simplesmente pulado — o chat NUNCA deve falhar por causa
de observabilidade (é um efeito colateral, não o caminho principal).

Quem cria os traces é `app/observability/tracing.py` (feature 002); este
módulo só cria o cliente.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

_client: Any = None
_client_initialized = False


def get_langfuse_client() -> Any:
    """Devolve o cliente Langfuse, ou `None` quando ele não está configurado."""
    global _client, _client_initialized
    if _client_initialized:
        return _client
    _client_initialized = True

    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.info("langfuse.disabled", extra={"reason": "missing_credentials"})
        return None

    try:
        from langfuse import Langfuse, is_langfuse_span

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            # O envio nunca pode segurar o chat (feature 002, FR-009).
            timeout=settings.langfuse_timeout_seconds,
            # Passado explicitamente: o pydantic-settings lê o .env sem exportá-lo
            # para as variáveis do processo, onde o SDK procuraria (research.md R14).
            environment=settings.langfuse_tracing_environment,
            # Só as observações criadas por tracing.py saem do processo; spans de
            # outras bibliotecas instrumentadas, com texto não sanitizado, não (R8).
            should_export_span=is_langfuse_span,
        )
    except Exception:  # noqa: BLE001 — tolerância a falha é intencional aqui
        logger.exception("langfuse.init_failed")
        _client = None
    return _client
