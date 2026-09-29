"""T049: limitador em memória, usado só quando o Upstash Redis falha.

Não é preciso nem compartilhado entre instâncias serverless — é
propositalmente mais restritivo que o limite normal, para reduzir risco de
custo enquanto o Redis estiver fora (fail-safe, ao contrário do guardrail
que é fail-open: aqui o risco é financeiro, não de experiência).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)

# Metade do limite normal, por instância — conservador de propósito.
_FALLBACK_LIMIT_PER_HOUR = 10
_WINDOW_SECONDS = 3600.0


def fallback_allow(visitor_key: str) -> bool:
    now = time.monotonic()
    with _lock:
        window = _hits[visitor_key]
        while window and now - window[0] > _WINDOW_SECONDS:
            window.popleft()
        if len(window) >= _FALLBACK_LIMIT_PER_HOUR:
            return False
        window.append(now)
        return True
