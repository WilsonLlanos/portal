"""T048: acumulador de custo diário e teto (FR-024).

Ao atingir `daily_cost_cap_cents`, o chat entra em estado "pausado" até a
virada do dia (UTC) — ver data-model.md § 3 DailyCost. Usa o mesmo Redis do
rate limit; se ele falhar, assume-se "não pausado" (fail-open aqui é
aceitável porque o rate limit por visitante já limita o dano, e travar o
chat inteiro por uma falha de infraestrutura seria pior para a experiência).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

_DAY_KEY_TTL_SECONDS = 60 * 60 * 48  # 48h, folga para fuso/relógio


def _today_key() -> str:
    return f"dailycost:{datetime.now(UTC).strftime('%Y-%m-%d')}"


class DailyCostTracker:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis = None
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            from upstash_redis import Redis

            self._redis = Redis(
                url=settings.upstash_redis_rest_url,
                token=settings.upstash_redis_rest_token,
            )
        # Fallback em memória (por instância), só para não quebrar em dev/CI
        # sem Redis configurado.
        self._local_total_cents = 0.0

    def is_paused(self) -> bool:
        total = self._read_total_cents()
        return total >= self._settings.daily_cost_cap_cents

    def add_cost(self, cents: float) -> None:
        if self._redis is None:
            self._local_total_cents += cents
            return
        try:
            key = _today_key()
            self._redis.incrbyfloat(key, cents)
            self._redis.expire(key, _DAY_KEY_TTL_SECONDS)
        except Exception:  # noqa: BLE001
            logger.exception("daily_cost.redis_write_failed")
            self._local_total_cents += cents

    def _read_total_cents(self) -> float:
        if self._redis is None:
            return self._local_total_cents
        try:
            value = self._redis.get(_today_key())
            return float(value) if value is not None else 0.0
        except Exception:  # noqa: BLE001
            logger.exception("daily_cost.redis_read_failed")
            return self._local_total_cents


_tracker: DailyCostTracker | None = None


def get_daily_cost_tracker() -> DailyCostTracker:
    global _tracker
    if _tracker is None:
        _tracker = DailyCostTracker(get_settings())
    return _tracker


def chat_status() -> str:
    """Usado por GET /health (T019)."""
    return "paused" if get_daily_cost_tracker().is_paused() else "active"
