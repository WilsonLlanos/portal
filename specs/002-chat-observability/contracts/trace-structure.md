# Contrato: estrutura do trace no Langfuse

Contrato entre o backend (que emite) e o painel e o juiz (que consomem). O juiz e os filtros do painel dependem destes **nomes e campos**: mudar qualquer um exige atualizar [judge-evaluator.md](judge-evaluator.md) e a regra configurada no Langfuse.

SDK: Langfuse Python 4.x, com observações explícitas (research.md R1).

## Atributos do trace

Aplicados com `propagate_attributes` na criação de cada observação (research.md R2):

| Atributo | Valor |
|---|---|
| `trace_name` | `"chat-turn"` |
| `session_id` | `conversation_id` (UUID), omitido quando ausente ou inválido |
| `metadata.lang` | `"pt-BR"` \| `"en"` |
| `metadata.kb_version` | `content_hash` do `manifest.json` (ou `"unknown"`) |

Ambiente: definido no cliente (`Langfuse(environment=...)`, a partir de `LANGFUSE_TRACING_ENVIRONMENT`), `"development"` ou `"production"` (research.md R14).

Trace I/O (`set_trace_io`): `input` = pergunta sanitizada; `output` = resposta final sanitizada (igual à raiz).

Todo texto que pode conter dado do visitante (pergunta, histórico e resposta) é gravado sanitizado, e quem sanitiza é o tracer (research.md R7). Nunca enviar: IP, user agent, `visitor_key`, `user_id`.

## Observações

### `chat-turn` (raiz, `as_type="span"`)

| Campo | Conteúdo |
|---|---|
| `input` | pergunta sanitizada (string) |
| `output` | resposta final sanitizada (string); parcial em erro; texto de recusa em `refused`; omitido em `rate_limited`/`paused` |
| `metadata.outcome` | `answered` \| `no_answer` \| `refused` \| `rate_limited` \| `paused` \| `error` |
| `metadata.environment` | `"development"` \| `"production"`, igual ao ambiente do cliente (filtro da regra do juiz) |
| `metadata.latency_ms` | inteiro |
| `metadata.client_disconnected` | `true` só quando o gerador foi fechado antes de o trace ser encerrado (visitante desconectou) |
| `level` | `DEFAULT`; `ERROR` em `error`; `WARNING` em desconexão |

**É a observação avaliada pelo juiz** (research.md R4).

### `guardrail` (`as_type="guardrail"`)

| Campo | Conteúdo |
|---|---|
| `input` | pergunta sanitizada |
| `output` | `{"decision": "allow" \| "block", "score": float \| null, "source": "model" \| "local" \| "skipped_degraded"}` |
| `level` | `WARNING` quando `source = "skipped_degraded"` |

### `embed-question` (`as_type="embedding"`)

| Campo | Conteúdo |
|---|---|
| `model` | `settings.gemini_embedding_model` |
| `input` | pergunta sanitizada |
| `level` / `status_message` | `ERROR` e a mensagem, se o embedding falhar |

### `retrieval` (`as_type="retriever"`)

| Campo | Conteúdo |
|---|---|
| `input` | `{"lang": "...", "top_k": 5}` |
| `output` | `[{"id": "<chunk id>", "score": float}, ...]`, em ordem decrescente |
| `metadata.top_score` | maior nota, ou ausente se não houve trechos |
| `level` / `status_message` | `ERROR` e a mensagem, se a busca falhar |

### `answer` (`as_type="generation"`)

| Campo | Conteúdo |
|---|---|
| `model` | `settings.gemini_model` |
| `model_parameters` | `{"temperature": 0.4, "max_output_tokens": 512}` (valores de `core/prompt.py`) |
| `input` | `[{"role": "system", "content": <system prompt>}, ...histórico sanitizado, {"role": "user", "content": <pergunta sanitizada>}]` |
| `output` | resposta sanitizada (completa, ou parcial em erro) |
| `completion_start_time` | instante do primeiro trecho de texto recebido do LLM |
| `usage_details` | `{"input": int, "output": int}` |
| `cost_details` | `{"input": usd, "output": usd, "total": usd}`, com os mesmos preços do teto diário |
| `level` / `status_message` | `ERROR` e `"llm_unavailable"` quando a geração falha |

## Scores

| Nome | Tipo | Quem grava | Alvo | Valor |
|---|---|---|---|---|
| `retrieval_top_score` | `NUMERIC` | backend (`root.score_trace`) | trace | maior nota da busca |
| `content_coverage` | `CATEGORICAL` | juiz do Langfuse | observação `chat-turn` | `respondeu` \| `lacuna` \| `recusa`, com justificativa em `comment` |

## Garantias de tolerância a falha

- Nenhuma chamada ao SDK pode lançar exceção para o pipeline; falhas viram log `observability.trace_failed`.
- Nenhum envio pela rede antes do primeiro token. O trace é encerrado localmente antes do último evento (`done` ou `error`), e o `flush()` roda depois dele: no próprio streaming ou, quando o primeiro evento já é um erro HTTP (429/503), numa `BackgroundTask` que roda depois da resposta (research.md R8).
- Visitante desconectado no meio do streaming: o `finally` do pipeline encerra o trace com `client_disconnected = true`, e o exportador em segundo plano do SDK o envia em melhor esforço, sem `flush` síncrono.
- Só observações criadas pela fachada são exportadas (`should_export_span=is_langfuse_span`); spans de outras bibliotecas instrumentadas nunca saem do processo.
- Sem chaves configuradas, o tracer é um Noop e o log JSON `chat.interaction` continua sendo emitido.
