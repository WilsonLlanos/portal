"""T047: rate limiter no Upstash Redis (FR-018).

Chave = hash(IP + user agent + sal do dia) — nunca o IP bruto (constituição,
Princípio IV — privacidade / data-model.md § 3 VisitorKey). Usa uma janela
fixa por hora (INCR + EXPIRE), suficiente para o volume de um portfólio.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.core.config import Settings
from app.limits.fallback import fallback_allow
from app.observability.logging import get_logger

logger = get_logger(__name__)

_WINDOW_SECONDS = 3600


def make_visitor_key(ip: str, user_agent: str) -> str:
    day_salt = datetime.now(UTC).strftime("%Y-%m-%d")
    digest = hashlib.sha256(f"{ip}|{user_agent}|{day_salt}".encode()).hexdigest()
    return f"ratelimit:{digest}"


class RateLimiter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis = None
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            from upstash_redis import Redis

            self._redis = Redis(
                url=settings.upstash_redis_rest_url,
                token=settings.upstash_redis_rest_token,
            )

    def allow(self, visitor_key: str) -> bool:
        if self._redis is None:
            return fallback_allow(visitor_key)

        try:
            count = self._redis.incr(visitor_key)
            if count == 1:
                self._redis.expire(visitor_key, _WINDOW_SECONDS)
            return count <= self._settings.rate_limit_per_hour
        except Exception:  # noqa: BLE001 — reserva local em caso de falha do Redis
            logger.exception("rate_limit.redis_failed")
            return fallback_allow(visitor_key)
