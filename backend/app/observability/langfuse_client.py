"""T022: cliente Langfuse tolerante a falha (FR-021/FR-022).

Se as chaves não estiverem configuradas, ou se o Langfuse estiver fora do
ar, o registro é simplesmente pulado — o chat NUNCA deve falhar por causa
de observabilidade (é um efeito colateral, não o caminho principal).
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

_client: Any = None
_client_initialized = False


def _get_client() -> Any:
    global _client, _client_initialized
    if _client_initialized:
        return _client
    _client_initialized = True

    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.info("langfuse.disabled", extra={"reason": "missing_credentials"})
        return None

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:  # noqa: BLE001 — tolerância a falha é intencional aqui
        logger.exception("langfuse.init_failed")
        _client = None
    return _client


def log_chat_interaction(**fields: Any) -> None:
    """Registra uma ChatInteraction (data-model.md § 3). `fields` NUNCA deve
    incluir dados pessoais do visitante (sem IP, sem user agent bruto).
    """
    client = _get_client()
    if client is None:
        # Sem Langfuse configurado: ainda registramos em log estruturado,
        # para não perder totalmente a observabilidade em dev/CI.
        logger.info("chat.interaction", extra=fields)
        return

    try:
        client.trace(name="chat.interaction", **fields)
    except Exception:  # noqa: BLE001
        logger.exception("langfuse.log_failed")
