"""T019: esqueleto do FastAPI (`GET /health`). O router do chat (`POST
/chat`) é adicionado em app/api/chat.py e incluído aqui (T052).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.observability.logging import configure_logging

configure_logging()

app = FastAPI(title="Portal de Portfólio — Backend do Chat")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _kb_version() -> str:
    """Hash do manifesto da base de conhecimento carregada (T019/T043)."""
    try:
        from app.retrieval.file_store import get_kb_manifest_hash

        return get_kb_manifest_hash()
    except Exception:  # noqa: BLE001 — /health nunca deve derrubar por isso
        return "unknown"


@app.get("/health")
def health() -> dict[str, str]:
    from app.guard.circuit_breaker import guard_circuit_status
    from app.limits.daily_cost import chat_status

    return {
        "status": "ok",
        "guard": guard_circuit_status(),
        "chat": chat_status(),
        "kb_version": _kb_version(),
    }


# O router do chat é importado por último para evitar import circular com
# módulos que, por sua vez, podem depender de `app.main` em testes.
from app.api.chat import router as chat_router  # noqa: E402

app.include_router(chat_router)
