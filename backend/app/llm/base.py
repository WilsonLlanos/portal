"""T015: interface `LLMClient` (constituição, Princípio VI — código
substituível). Qualquer provedor de LLM implementa este protocolo; o resto
do backend depende só dele. Ver specs/001-portfolio-portal/contracts/provider-interfaces.md.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class LLMChunk:
    text: str
    # Presente apenas no último fragmento do streaming.
    usage: Usage | None = None


class LLMUnavailable(Exception):
    """Erro do provedor de LLM — o chamador deve responder com a mensagem
    de indisponibilidade (FR-019), nunca deixar a exceção vazar ao visitante.
    """


class LLMClient(Protocol):
    def stream(
        self,
        *,
        system: str,
        messages: list[Message],
        temperature: float,
        max_output_tokens: int,
    ) -> Iterator[LLMChunk]:
        """Gera a resposta em streaming. Levanta LLMUnavailable em erro."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings para uma lista de textos. Levanta LLMUnavailable em erro."""
        ...
