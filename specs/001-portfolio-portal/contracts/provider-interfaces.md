# Contrato: interfaces de provedores (backend)

**Feature**: [spec.md](../spec.md) | **Constituição**: princípio VI (código substituível)

Os três provedores externos ficam atrás de interfaces pequenas (Python `Protocol`), escolhidas por configuração. O restante do código depende só destas interfaces. A assinatura abaixo é o contrato; a implementação fica para as tarefas.

## `LLMClient`

```python
class LLMClient(Protocol):
    def stream(self, *, system: str, messages: list[Message],
               temperature: float, max_output_tokens: int) -> Iterator[LLMChunk]: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

- `LLMChunk` tem `text` e, no último fragmento, `usage` (tokens de entrada/saída) para o cálculo de custo.
- Erros de provedor viram `LLMUnavailable` (o chat responde com a mensagem de indisponibilidade, FR-019).
- Implementação inicial: Gemini (`gemini-3.1-flash-lite`; embeddings Gemini). Alternativa prevista: Groq.

## `VectorStore`

```python
class VectorStore(Protocol):
    def search(self, query_embedding: list[float], lang: str, top_k: int) -> list[ScoredChunk]: ...
```

- `ScoredChunk` tem `chunk` (ver [data-model](../data-model.md)) e `score` (cosseno).
- Contrato de teste: dado um conjunto fixo de vetores, a busca retorna os `top_k` em ordem decrescente de similaridade e respeita o filtro de idioma.
- Implementação inicial: arquivo + NumPy. Alternativa prevista: Qdrant.

## `InputGuard`

```python
class InputGuard(Protocol):
    def check(self, text: str) -> GuardVerdict: ...
```

- `GuardVerdict` tem `decision` (`allow` | `block`), `score` (float ou `None`) e `source` (`model` | `local` | `skipped_degraded`).
- Nunca lança exceção para o chamador: falhas do serviço externo viram `skipped_degraded` (fail-open) com defesas locais mais restritas; o circuito abre após falhas consecutivas e fecha após um período de espera.
- Implementação inicial: Prompt Guard 2 86M via Groq + heurísticas locais. Alternativas previstas: ONNX local; LLM pequeno como classificador.

## Ordem do pipeline do chat

1. Validar tamanho e formato (FR-018).
2. Verificar teto diário (FR-024) e rate limit do visitante (FR-018).
3. `InputGuard.check` (FR-017); bloqueio gera resposta cordial de recusa.
4. Embutir a pergunta e `VectorStore.search` (filtro por idioma).
5. Montar o prompt (persona/tom, regras de veracidade, trechos recuperados, histórico validado) e `LLMClient.stream`.
6. Registrar a interação na observabilidade e acrescentar o custo ao acumulado diário.
