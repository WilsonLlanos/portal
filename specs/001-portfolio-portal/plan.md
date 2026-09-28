# Implementation Plan: Portal de Portfólio Profissional (IA)

**Branch**: `001-portfolio-portal` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-portfolio-portal/spec.md`

## Summary

Portal bilíngue (PT-BR/EN) e responsivo, com tema claro/escuro, que apresenta o autor a recrutadores e inclui um chat de IA (RAG) sobre a carreira do autor. Abordagem: **frontend Next.js 16 (React/TypeScript/Tailwind)** com conteúdo estático gerado em build a partir de arquivos versionados, e **backend FastAPI (Python)** com o pipeline do chat: validação, teto diário e rate limit (Upstash Redis), guardrail de entrada (Llama Prompt Guard 2 via Groq, fail-open com degradação), recuperação por embeddings pré-calculados com NumPy e geração com Gemini Flash-Lite, tudo atrás de interfaces substituíveis (`LLMClient`, `VectorStore`, `InputGuard`). Observabilidade com Langfuse. Hospedagem na Vercel (Hobby) em dois projetos; CI e automação com GitHub Actions. Detalhes e alternativas em [research.md](research.md).

## Technical Context

**Language/Version**: TypeScript 5.x sobre Node.js 24 (frontend, Next.js 16, React 19); Python 3.12 (backend)

**Primary Dependencies**: Frontend: Next.js 16, Tailwind CSS 4, `next-intl`, `next-themes`. Backend: FastAPI, `google-genai`, `groq` (ou `httpx`), `numpy`, `upstash-redis`, `langfuse`, `pydantic`. Gerenciadores: `npm` e `uv`.

**Storage**: sem banco de dados. Conteúdo em arquivos versionados (`frontend/content`); base de conhecimento em arquivos (`backend/data/kb`: `.npz` + JSON); estado efêmero no Upstash Redis (contadores e teto diário); rastreamento no Langfuse Cloud (retenção de 30 dias).

**Testing**: Backend: `pytest`, `ruff`, avaliação de referência (perguntas e ataques em `backend/tests/eval`). Frontend: Vitest + Testing Library, ESLint, `tsc`, Playwright (E2E + axe), Lighthouse CI.

**Target Platform**: Web (navegadores modernos, mobile-first); Vercel (Hobby) com dois projetos: `frontend/` e `backend/` (funções Python, Fluid compute).

**Project Type**: web-application (frontend + backend)

**Performance Goals**: Lighthouse > 90 (desempenho, acessibilidade, SEO); tela inicial renderizada estaticamente; primeiro token do chat em poucos segundos, com streaming.

**Constraints**: custo mensal próximo de zero (camadas gratuitas); bundle Python ≤ 500 MB; corpo de requisição/resposta ≤ 4,5 MB; guardrail com contexto de 512 tokens (limite de tamanho da pergunta compatível); nenhuma credencial no repositório.

**Scale/Scope**: tráfego de portfólio (dezenas a poucas centenas de visitas por mês); 1 página com 6 seções x 2 idiomas; base de conhecimento com dezenas a poucas centenas de trechos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Status |
|---|---|---|
| I. Veracidade | Prompt restrito aos trechos recuperados; resposta "não sei" cordial; conjunto de avaliação de referência (SC-003) | Passa |
| II. Custo mínimo | Camadas gratuitas (Vercel Hobby, Upstash, Langfuse Hobby, Gemini/Groq); rate limit, limite de tokens e teto diário de custo (FR-024); sem caching pago no MVP | Passa |
| III. Segurança em camadas | Prompt Guard 2 (Groq) + tamanho + heurísticas + rate limit + prompt restrito; fail-open com timeout e circuit breaker | Passa |
| IV. Privacidade | Sem IP bruto (hash com sal diário); Langfuse com 30 dias; aviso ao visitante; Gemini em camada paga (conteúdo não usado para treino) | Passa |
| V. Acessibilidade e desempenho | next-intl, next-themes, mobile-first, axe e Lighthouse CI | Passa |
| VI. Código didático e substituível | Interfaces `LLMClient`, `VectorStore`, `InputGuard` ([contrato](contracts/provider-interfaces.md)); comentários úteis em React | Passa |
| VII. CI/CD e automação | 6 workflows pequenos na ordem da constituição; deploy pela Vercel; `permissions:` mínimas; mitigação de desativação | Passa (ver nota N1) |
| VIII. Observabilidade e testes proporcionais | Langfuse + logs JSON + `/health`; testes na lógica crítica | Passa |
| IX. Gestão de credenciais | Segredos só em Vercel/GitHub Secrets; `.env.example`; chave do Google restrita com cota; secret scanning; sem endpoint próprio de guardrail para proteger | Passa |

**Nota N1**: a constituição cita "ping agendado". Com a mudança do guardrail para a Groq (não há Space que durma), o primeiro workflow passa a ser uma **verificação de saúde agendada** do backend em produção, que mantém o mesmo aprendizado (`schedule` + `curl` + falha explícita). É compatível com o texto do princípio VII, sem emenda.

**Gate pós-design**: reavaliado após Phase 1 — nenhuma violação; Complexity Tracking vazio.

## Decisões confirmadas (2026-09-27)

- **O1 - Cobrança do Gemini**: **faturamento ativado, com orçamento limitado.** O Gemini roda na camada paga (não usa o conteúdo dos visitantes para treinar modelos do Google), com um teto de gasto configurado diretamente no Google Cloud/AI Studio, além do teto diário próprio do chat (FR-024). Custo esperado: poucos dólares por mês no tráfego típico de um portfólio.
- **O2 - Prompt Guard 2 na Groq**: **cartão cadastrado na Groq.** Custo esperado irrisório (~US$ 0,04 por 25 M tokens). Mantém a arquitetura mais simples, com o modelo dedicado.
- **O3 - Limites do chat**: tamanho máximo da pergunta = **500 caracteres**; teto diário de custo = **US$ 0,50** (`DAILY_COST_CAP_CENTS=50`). Ambos configuráveis por variável de ambiente.

## Project Structure

### Documentation (this feature)

```text
specs/001-portfolio-portal/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── chat-api.openapi.yaml
│   └── provider-interfaces.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks - NÃO criado aqui)
```

### Source Code (repository root)

```text
frontend/                          # Projeto Vercel 1 (Root Directory: frontend)
├── app/
│   └── [locale]/                  # /pt-BR e /en
│       ├── layout.tsx
│       └── page.tsx               # composição das seções
├── components/
│   ├── sections/                  # Hero, Summary, Timeline, Projects, Certifications, Contact
│   ├── chat/                      # ChatPanel, mensagens, aviso de privacidade
│   └── ui/                        # seletor de idioma, alternador de tema, botões
├── content/
│   ├── pt-BR/                     # profile.json, timeline.json, projects.json, certifications.json, cv.md
│   └── en/
├── messages/                      # pt-BR.json, en.json (textos de interface)
├── lib/                           # carregamento/validação do conteúdo, cliente do chat (SSE)
├── public/                        # foto, cv/cv-pt-BR.pdf, cv/cv-en.pdf, imagens Open Graph
├── tests/                         # unit (Vitest) e e2e (Playwright)
├── next.config.ts                 # rewrite /api/* para o backend
└── package.json

backend/                           # Projeto Vercel 2 (Root Directory: backend)
├── app/
│   ├── main.py                    # FastAPI: /chat, /health
│   ├── api/                       # rotas e esquemas (pydantic)
│   ├── core/                      # configuração, pipeline do chat, prompt de sistema
│   ├── llm/                       # LLMClient + implementação Gemini
│   ├── retrieval/                 # VectorStore + implementação arquivo/NumPy
│   ├── guard/                     # InputGuard + Prompt Guard 2 (Groq) + heurísticas + circuit breaker
│   ├── limits/                    # rate limit, teto diário (Upstash Redis) e fallback em memória
│   └── observability/             # Langfuse, logs JSON
├── scripts/
│   └── ingest.py                  # gera data/kb a partir de ../frontend/content
├── data/kb/                       # chunks.json, vectors.npz, manifest.json (derivados, versionados)
├── tests/
│   ├── unit/                      # busca, guardrails, política de falha, limites, custo
│   └── eval/                      # perguntas e ataques de referência (SC-003, SC-007)
├── .env.example
└── pyproject.toml                 # gerenciado com uv

.github/
└── workflows/
    ├── health-check.yml           # agendado: /health em produção
    ├── frontend-ci.yml            # lint, typecheck, testes, build, Lighthouse CI
    ├── backend-ci.yml             # ruff, pytest
    └── ingest.yml                 # regenera embeddings quando frontend/content/** muda

.gitignore
brief.md
```

**Structure Decision**: aplicação web com **dois projetos independentes** (`frontend/` e `backend/`) no mesmo repositório, cada um implantado como um projeto Vercel. O frontend chama o backend pelo caminho `/api/*` (rewrite do Next.js), evitando CORS. O conteúdo tem uma única fonte de verdade em `frontend/content/`, usada pelo site (build) e pela ingestão (script), o que impede divergência entre o que o site mostra e o que o chat sabe. Ferramental do speckit/Claude fica fora do Git conforme o `.gitignore`.

## Complexity Tracking

| Desvio | Por que é necessário | Alternativa mais simples rejeitada porque |
|---|---|---|
| Dois projetos na Vercel (`frontend/` e `backend/`) em vez de um | Usar Python no backend (preferência do autor e objetivo de demonstrar IA) e Next.js no frontend | Um único projeto em TypeScript contrariaria a preferência do autor e o objetivo de aprendizado/demonstração em Python |
| Gemini e Groq em **camada paga** (com teto de orçamento) em vez da camada gratuita padrão, aparente exceção ao Princípio II (camadas gratuitas MUST ser priorizadas) | Gemini: a camada gratuita permite ao Google usar o conteúdo enviado para melhorar seus produtos, o que expõe as perguntas dos visitantes (Princípio IV, privacidade). Groq: a documentação não confirma o Prompt Guard 2 na camada 100% gratuita; cadastrar cartão evita risco de indisponibilidade sem aviso | A camada gratuita do Gemini foi rejeitada por conflitar com a privacidade dos visitantes; um guardrail alternativo sem custo (ONNX local, plano B do research.md D5) foi rejeitado por exigir mais esforço de implementação sem necessidade, já que o custo pago é irrisório (~US$0,04/25M tokens) e protegido pelo teto diário (FR-024) e pelo orçamento configurado no provedor (decisões O1/O2) — mantendo o espírito de custo mínimo do Princípio II mesmo fora da camada gratuita |

Nenhum outro desvio da constituição identificado; o restante do design passa nos 9 princípios sem exceção (ver Constitution Check acima).
