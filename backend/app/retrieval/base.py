"""T016: interface `VectorStore`. Ver
specs/001-portfolio-portal/contracts/provider-interfaces.md.
"""

from dataclasses import dataclass
from typing import Protocol

from app.retrieval.models import KnowledgeChunk, Lang


@dataclass(frozen=True)
class ScoredChunk:
    chunk: KnowledgeChunk
    score: float


class VectorStore(Protocol):
    def search(self, query_embedding: list[float], lang: Lang, top_k: int) -> list[ScoredChunk]:
        """Retorna os `top_k` trechos mais similares, em ordem decrescente de
        similaridade, filtrados por idioma.
        """
        ...
