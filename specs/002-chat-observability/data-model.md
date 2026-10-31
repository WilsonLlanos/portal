# Data Model: Observabilidade do Chat

Os dados desta feature vivem no **Langfuse Cloud** (retenção de 30 dias); nada é persistido no backend. A estrutura exata das observações está em [contracts/trace-structure.md](contracts/trace-structure.md). Este documento descreve as entidades, suas regras e como elas mudam conforme o outcome.

Substitui a entidade `ChatInteraction` de [001 data-model.md § 3](../001-portfolio-portal/data-model.md): os mesmos campos passam a viver na observação raiz e nas etapas do trace.

## Conversa

| Campo | Regra |
|---|---|
| `conversation_id` | UUID gerado no navegador uma vez por abertura da página, na primeira pergunta (`crypto.randomUUID()`), mantido só em memória; vira o `session_id` do Langfuse |

- Nasce na primeira pergunta depois de a página do chat ser aberta e morre ao fechar ou recarregar; não é gravada no navegador.
- Fica ausente quando o navegador não oferece `crypto.randomUUID`, o que acontece fora de HTTPS e de `localhost` (ex.: teste pelo IP da rede local); a pergunta é registrada sem sessão.
- Valor fora do formato UUID é descartado no backend (o trace fica sem sessão).
- Não identifica o visitante nem liga visitas diferentes (FR-008, FR-017).

## Registro da interação (trace + observação raiz `chat-turn`)

| Campo | Onde fica | Regra |
|---|---|---|
| `question` | `input` da raiz e do trace | pergunta **sanitizada** (R7) |
| `answer` | `output` da raiz e do trace | resposta final **sanitizada** (R7); texto parcial em caso de erro; texto de recusa quando recusada; omitida em `rate_limited` e `paused` |
| `outcome` | `metadata` da raiz | `answered` \| `no_answer` \| `refused` \| `rate_limited` \| `paused` \| `error` |
| `environment` | ambiente do cliente Langfuse e `metadata` da raiz | `development` \| `production` (R14) |
| `lang` | atributo propagado | idioma da sessão (`pt-BR` \| `en`) |
| `kb_version` | atributo propagado | `content_hash` do `manifest.json` da base |
| `session_id` | atributo propagado | `conversation_id`, quando válido |
| `latency_ms` | `metadata` da raiz | do recebimento da pergunta ao fim da resposta |
| `client_disconnected` | `metadata` da raiz | `true` quando o visitante fechou a conexão no meio do streaming, antes de o trace ser encerrado (com `level=WARNING`) |

Nome do trace: `chat-turn`. Perguntas vazias ou longas demais, rejeitadas antes de qualquer processamento, não geram trace (FR-001).

### Ciclo de vida (R8)

1. **Aberto** depois das validações de tamanho.
2. **Encerrado** localmente, sem rede, antes do último evento enviado ao visitante (`done` ou `error`).
3. **Enviado** (`flush`) depois do último evento: pelo próprio streaming, ou por uma tarefa em segundo plano quando a resposta é um erro HTTP (429/503).
4. Se o visitante desconecta no meio do streaming, o trace é encerrado com `client_disconnected = true` e enviado pelo exportador em segundo plano do SDK, em melhor esforço.

## Etapas (observações filhas da raiz)

| Etapa | Tipo | Dados principais |
|---|---|---|
| `guardrail` | `guardrail` | `decision` (`allow`/`block`), `score`, `source` (`model`/`local`/`skipped_degraded`) |
| `embed-question` | `embedding` | modelo de embedding; entrada = pergunta sanitizada |
| `retrieval` | `retriever` | lista `[{id, score}]` dos trechos, `top_score`, `top_k`, idioma do filtro |
| `answer` | `generation` | modelo, parâmetros, entrada (system prompt + histórico sanitizado + pergunta sanitizada), saída sanitizada, `usage_details`, `cost_details` (USD), `completion_start_time` |

Cada etapa tem início e fim próprios (a duração vem daí, FR-002).

## Scores

| Score | Tipo | Origem | Alvo |
|---|---|---|---|
| `retrieval_top_score` | numérico (−1 a 1) | backend, após a busca | trace |
| `content_coverage` | categórico: `respondeu` \| `lacuna` \| `recusa` | juiz configurado no Langfuse, com justificativa no `comment` | observação raiz `chat-turn` |

- `content_coverage = lacuna` é a fonte oficial das lacunas no conteúdo (FR-014); `recusa` nunca entra na lista.
- `retrieval_top_score` não é gravado quando a busca não devolve trechos.

## Etapas presentes por outcome

| Outcome | `guardrail` | `embed-question` | `retrieval` | `answer` | Avaliado pelo juiz |
|---|---|---|---|---|---|
| `answered` | ✓ | ✓ | ✓ | ✓ | sim |
| `no_answer` (busca vazia ou falha da busca) | ✓ | ✓ ou com erro | vazio ou com erro | ✓ | sim |
| `refused` (guardrail) | ✓ | — | — | — | não |
| `rate_limited` | — | — | — | — | não |
| `paused` (teto de custo) | — | — | — | — | não |
| `error` (LLM indisponível) | ✓ | ✓ | ✓ | ✓, com `level=ERROR` e saída parcial | não |

O juiz só avalia traces do ambiente `production` (R14).

## Sanitização (R7)

- Aplica-se à pergunta, a todas as mensagens do histórico e à resposta atual (completa, parcial ou de recusa) antes de entrar em qualquer observação. O visitante recebe a resposta original; só o registro é sanitizado.
- Quem sanitiza é o tracer, não o pipeline: o pipeline passa os textos originais.
- O system prompt e os trechos recuperados não são sanitizados (conteúdo público do autor).
- E-mails → `[email]`.
- Sequências com 9 ou mais dígitos (com espaços, pontos, traços ou parênteses entre eles) → `[número]`. Anos e intervalos de anos, como `2019-2024` (8 dígitos), são preservados.
- Nunca entram no trace: IP, user agent, `visitor_key` (hash do rate limit).
