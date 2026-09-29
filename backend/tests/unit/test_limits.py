"""T037: rate limit (~20/hora por visitante) e teto diário de custo
(US$ 0,50), com transição para "pausado" (FR-018, FR-024)."""

from app.core.config import Settings
from app.limits.daily_cost import DailyCostTracker
from app.limits.fallback import fallback_allow
from app.limits.rate_limit import RateLimiter, make_visitor_key


class _FakeRedis:
    def __init__(self):
        self._counters: dict[str, float] = {}

    def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return int(self._counters[key])

    def incrbyfloat(self, key: str, amount: float) -> float:
        self._counters[key] = self._counters.get(key, 0.0) + amount
        return self._counters[key]

    def expire(self, key: str, seconds: int) -> None:  # noqa: ARG002
        pass

    def get(self, key: str):
        return self._counters.get(key)


def test_rate_limiter_allows_up_to_configured_limit_then_blocks():
    settings = Settings(rate_limit_per_hour=20)
    limiter = RateLimiter(settings)
    limiter._redis = _FakeRedis()
    key = make_visitor_key("203.0.113.1", "pytest-agent")

    results = [limiter.allow(key) for _ in range(21)]

    assert results[:20] == [True] * 20
    assert results[20] is False  # a 21ª requisição na mesma hora é bloqueada


def test_fallback_limiter_used_when_redis_unavailable():
    settings = Settings()  # sem credenciais Upstash -> client None
    limiter = RateLimiter(settings)
    assert limiter._redis is None  # confirma que caiu no caminho de fallback

    key = make_visitor_key("203.0.113.2", "pytest-agent")
    # Não deve levantar exceção e deve respeitar algum limite conservador.
    results = [limiter.allow(key) for _ in range(15)]
    assert False in results


def test_daily_cost_tracker_pauses_at_cap():
    settings = Settings(daily_cost_cap_cents=50)
    tracker = DailyCostTracker(settings)
    tracker._redis = _FakeRedis()

    assert tracker.is_paused() is False
    tracker.add_cost(30)
    assert tracker.is_paused() is False
    tracker.add_cost(20)  # total = 50 == cap
    assert tracker.is_paused() is True


def test_fallback_allow_has_its_own_conservative_limit():
    key = "isolated-fallback-key"
    results = [fallback_allow(key) for _ in range(11)]
    assert results[:10] == [True] * 10
    assert results[10] is False
