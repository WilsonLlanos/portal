# Implementation Plan: Observabilidade do Chat com Trace Completo e Avaliação Automática

**Branch**: `002-chat-observability` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-chat-observability/spec.md`

## Summary

Cada pergunta do chat passa a gerar um **trace completo** no Langfuse, no lugar do evento único atual. O trace tem uma observação raiz `chat-turn` (pergunta sanitizada → resposta sanitizada, outcome) e uma etapa por passo do pipeline: `guardrail`, `embed-question`, `retrieval` (trechos e notas) e `answer` (geração com modelo, tokens, custo e tempo até o primeiro token). A maior nota da busca vira o score numérico `retrieval_top_score`. As perguntas de uma conversa são agrupadas por um `conversation_id` aleatório, gerado no navegador.

Um **juiz LLM** configurado no painel do Langfuse, com uma chave do Gemini exclusiva, avalia a raiz `chat-turn` dos traces de produção e grava o score categórico `content_coverage` (`respondeu` / `lacuna` / `recusa`). Esse score passa a ser a fonte das lacunas no conteúdo.

Abordagem técnica: observações explícitas do SDK v4, sem contexto implícito, por causa do pipeline em gerador com streaming. A instrumentação fica atrás de uma fachada `ChatTracer` com implementação Noop, que também sanitiza todo texto vindo do visitante. Toda chamada ao SDK é tolerante a falha. O trace é encerrado localmente antes do último evento e enviado (`flush`) depois dele: no próprio streaming, ou numa `BackgroundTask` quando a resposta é um erro HTTP. Desenvolvimento e produção usam chaves e ambientes separados. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend); TypeScript 5.x / React 19 (frontend, mudança mínima)

**Primary Dependencies**: `langfuse` 4.15.6 (já instalado; SDK baseado em OpenTelemetry), FastAPI, `google-genai`. Nenhuma dependência nova.

**Storage**: nenhum no projeto. Traces e scores ficam no Langfuse Cloud (Hobby, retenção de 30 dias).

**Testing**: `pytest` (unidade: tracer com dublê do SDK, sanitização, validação do `conversation_id`; contrato: `POST /api/chat` com o campo novo e o envio do trace nas respostas 429/503); avaliação com chamadas reais em `tests/eval/test_judge_accuracy.py` (SC-004, fora do CI); Vitest para o envio do `conversation_id` no frontend.

**Target Platform**: Vercel (funções Python do backend, serverless); Langfuse Cloud.

**Project Type**: web-application (frontend + backend), igual à feature 001.

**Performance Goals**: nenhum envio pela rede ao Langfuse antes do primeiro token (verificado em teste de unidade); o tempo até a primeira palavra varia no máximo 10% com o Langfuse fora do ar (SC-003, medido no cenário 8 do quickstart).

**Constraints**: plano Hobby (50 mil unidades por mês, sem excedente; cerca de 10 unidades por pergunta respondida, incluindo o trace do juiz); juiz abaixo de US$ 0,50 por mês com 1.000 perguntas; sem dados pessoais no trace; o pipeline é um gerador iterado em threads diferentes (nenhum contexto OpenTelemetry pode atravessar um `yield`).

**Scale/Scope**: tráfego de portfólio (dezenas a poucas centenas de perguntas por mês); 5 observações e 2 scores por pergunta respondida.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Status |
|---|---|---|
| I. Veracidade | O juiz não interfere nas respostas: roda depois, fora do backend, e só classifica | Passa |
| II. Custo mínimo | Langfuse Hobby (gratuito); juiz com modelo Flash-Lite, cota própria e amostragem configurável; nenhuma dependência nova | Passa |
| III. Segurança em camadas | Sem mudança nas defesas; o `conversation_id` é validado como UUID para não virar canal de texto livre; a pergunta é tratada como dado no critério do juiz | Passa |
| IV. Privacidade | Sanitização da pergunta, do histórico e da resposta registrada (e-mails e sequências de 9+ dígitos), feita pelo tracer; `conversation_id` efêmero e não persistido; nunca IP, user agent nem `visitor_key`; retenção de 30 dias | Passa |
| V. Acessibilidade e desempenho | Nenhuma mudança visível na interface; nada do Langfuse no caminho até o primeiro token | Passa |
| VI. Código didático e substituível | Fachada `ChatTracer` com implementações Langfuse e Noop, no mesmo padrão de `LLMClient`/`VectorStore`/`InputGuard`; comentários explicando por que não usar contexto implícito | Passa |
| VII. CI/CD | Testes de unidade e contrato sem rede (Noop ou dublê do SDK) rodam no CI; avaliação com chamadas reais fica local, como os demais `tests/eval` | Passa |
| VIII. Observabilidade e testes proporcionais | É a própria feature: rastreia pergunta, trechos, guardrail, latência, custo e erros, conforme o princípio exige | Passa |
| IX. Gestão de credenciais | Chave do juiz exclusiva, restrita à Generative Language API, num projeto do Google Cloud próprio (cota e faturamento separados), guardada só no cofre do Langfuse (LLM connection); dois pares de chaves do Langfuse, um para desenvolvimento (`.env`) e outro para produção (Vercel), com ambientes `development` e `production` (R14) | Passa |

**Gate pós-design** (reavaliado após a Phase 1): nenhuma violação. Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

```text
specs/002-chat-observability/
├── plan.md              # Este arquivo
├── research.md          # Phase 0: decisões R1–R14
├── data-model.md        # Phase 1: entidades, scores, etapas por outcome
├── quickstart.md        # Phase 1: configuração do Langfuse e do juiz + 10 cenários de validação
├── contracts/
│   ├── trace-structure.md   # nomes, tipos e campos das observações e scores
│   ├── chat-api-delta.md    # campo conversation_id em POST /api/chat
│   └── judge-evaluator.md   # conexão, avaliador, critério e regra do juiz
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — não criado aqui)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── schemas.py              # + ChatRequest.conversation_id (UUID opcional, inválido → None)
│   │   └── chat.py                 # repassa conversation_id; em erro HTTP, consome o resto do gerador numa BackgroundTask
│   ├── core/
│   │   ├── config.py               # + langfuse_timeout_seconds, langfuse_tracing_environment
│   │   └── pipeline.py             # instrumentação via ChatTracer; finish antes do último evento, flush depois; finally só na desconexão
│   └── observability/
│       ├── tracing.py              # NOVO: ChatTracer, LangfuseChatTurnTrace, NoopChatTurnTrace (sanitiza todo texto do visitante)
│       ├── sanitize.py             # NOVO: sanitização (movida de pipeline.py, regra de 9+ dígitos)
│       ├── judge_prompt.md         # NOVO: critério do juiz (fonte única para o painel e o teste)
│       └── langfuse_client.py      # cliente com timeout=2, environment e should_export_span; log_chat_interaction removido
├── tests/
│   ├── unit/
│   │   ├── test_tracing.py         # NOVO: estrutura do trace por outcome, tolerância a falha, Noop
│   │   └── test_sanitize.py        # NOVO: e-mails, telefones, CPF, datas preservadas
│   ├── contract/
│   │   └── test_chat_api.py        # + conversation_id válido, inválido e ausente
│   └── eval/
│       ├── judge_reference.jsonl   # NOVO: 21+ pares rotulados (7 por categoria)
│       └── test_judge_accuracy.py  # NOVO: SC-004 com GEMINI_JUDGE_API_KEY
└── .env.example                    # LANGFUSE_TIMEOUT_SECONDS, LANGFUSE_TRACING_ENVIRONMENT; comentário sobre a chave do juiz (fica no Langfuse, não aqui)

frontend/
├── components/chat/useChatSession.ts   # conversation_id gerado na primeira pergunta (useRef), omitido sem crypto.randomUUID
└── tests/unit/                          # + teste do envio do conversation_id

specs/001-portfolio-portal/
├── contracts/chat-api.openapi.yaml      # + conversation_id
└── data-model.md                        # § 3 ChatInteraction aponta para a feature 002
```

**Structure Decision**: mantém a estrutura de dois projetos da feature 001. A instrumentação fica concentrada em `backend/app/observability/`, e o pipeline só chama métodos da fachada `ChatTracer`, sem importar o SDK do Langfuse nem sanitizar textos. O `chat.py` só muda para repassar o `conversation_id` e garantir o envio do trace nas respostas de erro HTTP. O frontend só ganha o envio do `conversation_id`. O juiz é configuração do Langfuse, documentada no quickstart; o único artefato dele no repositório é o `judge_prompt.md`, mais o teste que o valida.

## Complexity Tracking

Nenhuma violação da constituição; nada a justificar.
