"""T017: interface `InputGuard`. Ver
specs/001-portfolio-portal/contracts/provider-interfaces.md.

Contrato importante: `check` nunca lança exceção para o chamador. Falhas do
serviço externo viram `GuardVerdict(decision="allow", source="skipped_degraded")`
— é assim que o fail-open (constituição, Princípio III) é implementado.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

Decision = Literal["allow", "block"]
Source = Literal["model", "local", "skipped_degraded"]


@dataclass(frozen=True)
class GuardVerdict:
    decision: Decision
    score: float | None
    source: Source


class InputGuard(Protocol):
    def check(self, text: str) -> GuardVerdict: ...
