"""T046: circuit breaker simples para o InputGuard externo (Groq).

Evita esperar o timeout a cada pergunta enquanto o serviço estiver fora:
depois de `failure_threshold` falhas seguidas, o circuito "abre" e as
chamadas são puladas (fail-open, ver guard/base.py) por `reset_seconds`,
quando volta a tentar (half-open).
"""

from __future__ import annotations

import threading
import time


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_seconds: float = 60.0) -> None:
        self._failure_threshold = failure_threshold
        self._reset_seconds = reset_seconds
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    def is_open(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return False
            if time.monotonic() - self._opened_at >= self._reset_seconds:
                # Half-open: permite uma nova tentativa.
                self._opened_at = None
                self._consecutive_failures = 0
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._failure_threshold:
                self._opened_at = time.monotonic()

    @property
    def status(self) -> str:
        return "degraded" if self.is_open() else "normal"


# Instância única do processo — cada instância de função serverless tem a
# sua (não é compartilhada entre invocações "frias", o que é aceitável:
# o pior caso é uma tentativa extra ocasional contra o Groq).
guard_circuit_breaker = CircuitBreaker()


def guard_circuit_status() -> str:
    return guard_circuit_breaker.status
