# Tasks: Portal de Portfólio Profissional (IA)

**Input**: Design documents from `specs/001-portfolio-portal/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: incluídas para a lógica crítica (busca, guardrail, limites, rota do chat) e para os fluxos principais de UI, conforme o princípio VIII da constituição ("testes proporcionais... cobrem a lógica crítica em vez de perseguir cobertura total"). Não há TDD estrito para todos os componentes visuais.

**Organization**: tarefas agrupadas por história de usuário (spec.md), para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: história de usuário à qual a tarefa pertence (US1–US5)
- Caminhos de arquivo exatos em cada descrição

## Path Conventions

Aplicação web com dois projetos (ver [plan.md](plan.md) § Project Structure):
- `frontend/` — Next.js 16 (App Router), TypeScript, Tailwind
- `backend/` — FastAPI (Python 3.12, `uv`)
- `.github/workflows/` — GitHub Actions

---

## Phase 1: Setup

**Purpose**: inicialização dos dois projetos e do repositório

- [x] T001 Criar a estrutura de pastas `frontend/`, `backend/`, `.github/workflows/` conforme [plan.md](plan.md) § Project Structure
- [x] T002 [P] Inicializar projeto Next.js 16 (App Router, TypeScript, Tailwind CSS 4) em `frontend/`, com `frontend/package.json` e `frontend/tsconfig.json`
- [x] T003 [P] Inicializar projeto Python com `uv` em `backend/` (`backend/pyproject.toml`), com dependências: `fastapi`, `google-genai`, `groq`, `numpy`, `upstash-redis`, `langfuse`, `pydantic`, `pydantic-settings`
- [x] T004 [P] Configurar ESLint, Prettier e `tsc --noEmit` em `frontend/` (`frontend/.eslintrc.json` ou `eslint.config.mjs`)
- [x] T004a [P] Configurar Vitest + Testing Library em `frontend/` (`frontend/vitest.config.ts`, script `test` em `frontend/package.json`), para os testes unitários de componentes e de lógica de conteúdo
- [x] T005 [P] Configurar `ruff` em `backend/pyproject.toml` (lint e format)
- [x] T006 Criar `backend/.env.example` com todas as variáveis: `GEMINI_API_KEY`, `GROQ_API_KEY`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `MAX_MESSAGE_LENGTH=500`, `DAILY_COST_CAP_CENTS=50`, `RATE_LIMIT_PER_HOUR=20`, `GUARD_TIMEOUT_SECONDS=2` (sem valores reais; ver constituição IX)
- [x] T007 Atualizar o `.gitignore` da raiz com os artefatos de build de `frontend/` (`frontend/.next/`, `frontend/node_modules/`) e `backend/` (`backend/.venv/`, `backend/__pycache__/`), preservando as regras já existentes
- [x] T007a [P] Configurar um teto de orçamento (alerta e/ou corte) na conta paga do Google Cloud/AI Studio usada pelo `GEMINI_API_KEY`, conforme a decisão O1 do [plan.md](plan.md) (não é código; registrar no `README.md` que esse passo foi feito e o valor configurado)
- [ ] T007b [P] Cadastrar um cartão na conta da Groq usada pelo `GROQ_API_KEY` e confirmar o preço vigente do `meta-llama/llama-prompt-guard-2-86m`, conforme a decisão O2 do [plan.md](plan.md) (não é código; registrar no `README.md` que esse passo foi feito)

**Checkpoint**: os dois projetos instalam e rodam localmente (mesmo sem funcionalidade).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: infraestrutura que TODAS as histórias de usuário exigem

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase estar completa.

- [x] T008 Definir o esquema de conteúdo (TypeScript) para `Profile`, `Experience`, `Project`, `Certification` em `frontend/lib/content/schema.ts`, replicando os campos e regras de [data-model.md](data-model.md) § 1 (ex.: `Experience.start`/`end` no formato `YYYY-MM`, `end = null` = em andamento, `start <= end`; `Project.technologies` com pelo menos 1 item; `alt` obrigatório em `profile.photo`)
- [x] T009 [P] Criar os arquivos de conteúdo provisório `frontend/content/pt-BR/{profile,timeline,projects,certifications}.json` e `frontend/content/pt-BR/cv.md`, claramente marcados como placeholder, seguindo o esquema de T008
- [x] T010 [P] Criar os arquivos equivalentes em `frontend/content/en/{profile,timeline,projects,certifications}.json` e `frontend/content/en/cv.md`, com os mesmos IDs de `T009` (necessário para o edge case "idioma sem tradução")
- [x] T009b [P] Mover `FotoPerfil.png` (raiz do repositório) para `frontend/public/images/profile.png` e referenciá-la em `profile.json` (pt-BR e en, via `T009`/`T010`), com `alt` descritivo em cada idioma — conteúdo real já fornecido pelo autor, não é mais placeholder
- [x] T010a [P] Mover os CVs reais fornecidos na raiz do repositório para `frontend/public/cv/`, renomeando `CV_Wilson_Llanos_AI.pdf` → `cv-pt-BR.pdf` e `CV_Wilson_Llanos_AI-En.pdf` → `cv-en.pdf` (conteúdo real já fornecido pelo autor, não é mais placeholder; necessário para T025 e para o cenário 1 do [quickstart.md](quickstart.md)) (FR-006)
- [x] T011 Implementar o carregador e validador de conteúdo em `frontend/lib/content/loader.ts`, que falha o build se um idioma estiver com campos ausentes frente ao outro (edge case da spec)
- [x] T011a [P] Teste unitário (Vitest) do carregador de conteúdo em `frontend/tests/unit/content-loader.test.ts`, cobrindo o caso do edge case "idioma sem tradução" (falha quando um campo existe em um idioma e falta no outro) (depende de T011, T004a)
- [x] T012 Configurar roteamento `next-intl` para os locais `pt-BR` e `en` em `frontend/i18n/request.ts` e `frontend/middleware.ts`, com `pt-BR` como alternativa quando o navegador não corresponder (Assumptions da spec)
- [x] T013 Criar `frontend/app/[locale]/layout.tsx` com `next-themes` (tema padrão = preferência do sistema, com troca manual persistida) e os textos de interface de `frontend/messages/{pt-BR,en}.json`
- [x] T014 [P] Definir as configurações do backend (Pydantic `BaseSettings`) em `backend/app/core/config.py`, lendo as variáveis de `T006`
- [x] T015 [P] Definir o protocolo `LLMClient` (`stream`, `embed`) em `backend/app/llm/base.py`, conforme [contracts/provider-interfaces.md](contracts/provider-interfaces.md)
- [x] T016 [P] Definir o protocolo `VectorStore` (`search`) e `ScoredChunk` em `backend/app/retrieval/base.py`, conforme [contracts/provider-interfaces.md](contracts/provider-interfaces.md)
- [x] T017 [P] Definir o protocolo `InputGuard` (`check`) e `GuardVerdict` (`decision: allow|block`, `score`, `source: model|local|skipped_degraded`) em `backend/app/guard/base.py`, conforme [contracts/provider-interfaces.md](contracts/provider-interfaces.md)
- [x] T018 [P] Implementar o modelo `KnowledgeChunk` (`id`, `lang`, `source`, `source_id`, `text`, `embedding`) em `backend/app/retrieval/models.py`, conforme [data-model.md](data-model.md) § 2
- [x] T019 Criar o esqueleto do FastAPI em `backend/app/main.py` com `GET /health` retornando `HealthResponse` (`status`, `guard`, `chat`, `kb_version`), conforme [contracts/chat-api.openapi.yaml](contracts/chat-api.openapi.yaml)
- [x] T020 Configurar o rewrite `/api/*` → backend em `frontend/next.config.ts`, para o frontend chamar o backend sem CORS
- [x] T021 [P] Configurar logging estruturado em JSON em `backend/app/observability/logging.py`
- [x] T022 [P] Implementar o cliente Langfuse (assíncrono, tolerante a falha de rede) em `backend/app/observability/langfuse_client.py`
- [x] T022a [P] Configurar `frontend/playwright.config.ts` com projetos para **mobile** (viewport ~375px, ex. dispositivo Pixel 5) e **desktop** (viewport ~1280px), para que todo teste E2E rode nos dois formatos automaticamente, sem precisar fixar viewport em cada arquivo de teste
- [x] T022b [P] Instalar `@axe-core/playwright` e criar o helper `frontend/tests/e2e/utils/axe.ts` (função reutilizável que roda a checagem de acessibilidade sobre a página atual), para ser chamado a partir de qualquer spec de E2E

**Checkpoint**: fundação pronta — as histórias de usuário podem começar.

---

## Phase 3: User Story 1 - Conhecer o autor na tela inicial (Priority: P1) 🎯 MVP

**Goal**: o recrutador vê, sem rolar a página, foto, nome, título, frase de posicionamento e os botões "Baixar CV" e "Falar comigo" (FR-001, FR-006).

**Independent Test**: abrir o portal em celular e desktop e confirmar que os elementos do hero aparecem sem rolagem e que "Baixar CV" entrega o PDF certo.

### Tests for User Story 1

- [x] T023 [P] [US1] Teste Playwright: hero visível sem rolagem (mobile e desktop cobertos pelos projetos configurados em `T022a`) e sem violações de acessibilidade (via o helper de `T022b`) em `frontend/tests/e2e/hero.spec.ts` (Acceptance Scenario 1 da US1; depende de T022a, T022b)

### Implementation for User Story 1

- [x] T024 [P] [US1] Criar o componente `Hero` em `frontend/components/sections/Hero.tsx` (foto com `alt`, nome, título, frase, botões "Baixar CV" e "Falar comigo"), consumindo `profile.json` via `T011`
- [x] T025 [US1] Ligar "Baixar CV" ao arquivo `frontend/public/cv/cv-{locale}.pdf` do idioma atual (depende de T010a; FR-006)
- [x] T026 [US1] Ligar "Falar comigo" à navegação até a seção de contato (Acceptance Scenario 3 da US1)
- [x] T027 [US1] Adicionar metadados Open Graph e de SEO por idioma em `frontend/app/[locale]/layout.tsx` (FR-012)
- [x] T028 [US1] Montar `frontend/app/[locale]/page.tsx`, posicionando o `Hero` como primeira seção

**Checkpoint**: User Story 1 funcional e testável de forma independente — MVP entregável.

---

## Phase 4: User Story 2 - Ver a trajetória, projetos e certificações (Priority: P1)

**Goal**: o recrutador lê o resumo de carreira, a linha do tempo, os projetos (com link do GitHub) e as certificações (FR-002 a FR-005).

**Independent Test**: navegar pelas seções e confirmar que cada item de experiência, projeto e certificação aparece com seus dados, e que os links de projeto levam ao repositório correto.

### Tests for User Story 2

- [x] T029 [P] [US2] Teste Playwright: resumo, linha do tempo (ordem cronológica), projetos (link do GitHub) e certificações renderizam com os dados do conteúdo, e sem violações de acessibilidade (via o helper de `T022b`), em `frontend/tests/e2e/content-sections.spec.ts` (mobile e desktop cobertos pelos projetos de `T022a`)

### Implementation for User Story 2

- [x] T030 [P] [US2] Criar o componente `Summary` em `frontend/components/sections/Summary.tsx` (FR-002)
- [x] T031 [P] [US2] Criar o componente `Timeline` em `frontend/components/sections/Timeline.tsx`, ordenando por `start` decrescente (FR-003; regra de ordenação de [data-model.md](data-model.md))
- [x] T032 [P] [US2] Criar o componente `Projects` em `frontend/components/sections/Projects.tsx` (cards com descrição, tecnologias e link do repositório) (FR-004)
- [x] T033 [P] [US2] Criar o componente `Certifications` em `frontend/components/sections/Certifications.tsx` (FR-005)
- [x] T034 [US2] Adicionar as quatro seções a `frontend/app/[locale]/page.tsx`, após o `Hero` (depende de T028)

**Checkpoint**: User Stories 1 e 2 funcionam juntas e de forma independente.

---

## Phase 5: User Story 3 - Conversar com o chat de IA sobre a carreira do autor (Priority: P2)

**Goal**: o chat responde com base no conteúdo do autor, em tom simpático e profissional, admite quando não sabe, recusa manipulação, respeita limites de tamanho/uso/custo e degrada com segurança se o guardrail falhar (FR-013 a FR-024).

**Independent Test**: fazer perguntas cobertas e não cobertas pelo conteúdo, tentar manipular o chat, estourar o limite por visitante e o teto diário, e derrubar o guardrail — verificando os 7 Acceptance Scenarios da US3.

### Tests for User Story 3

- [x] T035 [P] [US3] Testes unitários do `VectorStore` (arquivo/NumPy): ordena por similaridade decrescente e respeita o filtro de idioma, em `backend/tests/unit/test_vector_store.py`
- [x] T036 [P] [US3] Testes unitários do `InputGuard`: `skipped_degraded` em timeout/erro (fail-open) e abertura/fechamento do circuit breaker, em `backend/tests/unit/test_input_guard.py`
- [x] T037 [P] [US3] Testes unitários de limites: rate limit de ~20 perguntas/hora por visitante e teto diário de US$ 0,50 com transição para `pausado`, em `backend/tests/unit/test_limits.py` (FR-018, FR-024)
- [x] T038 [P] [US3] Teste de contrato de `POST /api/chat` e `GET /api/health` contra [contracts/chat-api.openapi.yaml](contracts/chat-api.openapi.yaml) (códigos 200/400/429/503) em `backend/tests/contract/test_chat_api.py`
- [x] T039 [US3] Conjunto de perguntas de referência (PT/EN) em `backend/tests/eval/questions.jsonl` e execução em `backend/tests/eval/test_answer_accuracy.py`, validando SC-003 (≥95% corretas; 100% das sem resposta admitidas)
- [x] T040 [US3] Conjunto de ataques de referência (prompt injection/jailbreak, PT/EN) em `backend/tests/eval/attacks.jsonl` e execução em `backend/tests/eval/test_guard_resistance.py`, validando SC-007

### Implementation for User Story 3

- [x] T041 [US3] Script de ingestão `backend/scripts/ingest.py`: lê `frontend/content/{lang}/*`, gera trechos de ~150–300 tokens e grava `backend/data/kb/{chunks.json,vectors.npz,manifest.json}` (depende de T009, T010, T018)
- [x] T042 [P] [US3] Implementar `GeminiLLMClient` (`stream` com `gemini-3.1-flash-lite`, temperatura 0,3–0,5; `embed`) em `backend/app/llm/gemini.py`, na camada paga (decisão O1 do plano)
- [x] T043 [P] [US3] Implementar `FileVectorStore` (NumPy, similaridade de cosseno, filtro por idioma) em `backend/app/retrieval/file_store.py`, falhando na inicialização se `manifest.json` não corresponder ao modelo de embedding configurado
- [x] T044 [P] [US3] Implementar `GroqPromptGuard` (`meta-llama/llama-prompt-guard-2-86m`, timeout de `GUARD_TIMEOUT_SECONDS`) em `backend/app/guard/prompt_guard.py`
- [x] T045 [P] [US3] Implementar guarda local de reforço (heurísticas + limite de tamanho) em `backend/app/guard/heuristics.py`, usada quando degradado
- [x] T046 [P] [US3] Implementar o circuit breaker (abre após N falhas consecutivas, fecha após espera) em `backend/app/guard/circuit_breaker.py`
- [x] T047 [P] [US3] Implementar o rate limiter no Upstash Redis (chave = hash de IP+user agent+sal diário, sem IP bruto; ~20 req/hora) em `backend/app/limits/rate_limit.py`
- [x] T048 [P] [US3] Implementar o acumulador de custo diário e o teto de US$ 0,50 (`DailyCost`, estado `pausado`↔`ativo`) em `backend/app/limits/daily_cost.py`
- [x] T049 [US3] Implementar o limitador de memória local como reserva se o Redis falhar, em `backend/app/limits/fallback.py`
- [x] T050 [US3] Escrever o prompt de sistema (persona simpática/comercial, regras de veracidade, recusa de manipulação sem revelar instruções, sugestão de próximos passos) em `backend/app/core/prompt.py` (FR-014, FR-015, FR-017)
- [x] T051 [US3] Compor o pipeline do chat em `backend/app/core/pipeline.py`, na ordem de [contracts/provider-interfaces.md](contracts/provider-interfaces.md): validar tamanho (500 caracteres) → teto diário → rate limit → `InputGuard` → `VectorStore.search` → montar prompt com histórico validado (até 4 trocas) → `LLMClient.stream` → registrar interação
- [x] T052 [US3] Implementar `POST /api/chat` (SSE) em `backend/app/api/chat.py`, conforme [contracts/chat-api.openapi.yaml](contracts/chat-api.openapi.yaml) (eventos `token`/`done`/`error`; respostas 400/429/503 cordiais com alternativa de contato/CV)
- [x] T053 [US3] Registrar cada `ChatInteraction` no Langfuse (pergunta sanitizada, idioma, `retrieved_chunk_ids`, `guard_result`, tokens, custo, latência, `outcome`), sem dados pessoais, dentro do pipeline (depende de T051, T022)
- [x] T054 [P] [US3] Criar o cliente de chat (SSE) e o estado de sessão (últimas 4 trocas, só em memória do navegador) em `frontend/components/chat/useChatSession.ts`
- [x] T055 [P] [US3] Criar o componente `ChatPanel` (streaming, sugestões de próximo passo) em `frontend/components/chat/ChatPanel.tsx`
- [x] T056 [US3] Criar o aviso de privacidade e as mensagens de limite/pausa/indisponibilidade em `frontend/components/chat/ChatNotices.tsx` (FR-019, FR-022)
- [x] T057 [US3] Adicionar o `ChatPanel` a `frontend/app/[locale]/page.tsx` (depende de T034)

**Checkpoint**: User Stories 1 a 3 funcionam juntas e de forma independente.

---

## Phase 6: User Story 4 - Usar o portal em PT-BR ou EN e nos temas claro e escuro (Priority: P2)

**Goal**: o visitante troca idioma e tema, com a escolha mantida e refletida no conteúdo, no CV e no chat (FR-008, FR-009, FR-016).

**Independent Test**: alternar idioma e tema, navegar e recarregar, confirmando que tudo muda e persiste.

### Tests for User Story 4

- [x] T058 [P] [US4] Teste Playwright: trocar idioma e tema, navegar e recarregar, confirmando persistência e tema inicial = preferência do sistema, em `frontend/tests/e2e/locale-theme.spec.ts` (mobile e desktop cobertos pelos projetos de `T022a`)

### Implementation for User Story 4

- [x] T059 [P] [US4] Criar o componente `LanguageSwitcher` em `frontend/components/ui/LanguageSwitcher.tsx`
- [x] T060 [P] [US4] Criar o componente `ThemeToggle` em `frontend/components/ui/ThemeToggle.tsx`
- [x] T061 [US4] Passar o idioma selecionado como `lang` em cada chamada de `POST /api/chat` em `frontend/components/chat/useChatSession.ts` (depende de T054; FR-016)

**Checkpoint**: User Stories 1 a 4 funcionam juntas e de forma independente.

---

## Phase 7: User Story 5 - Entrar em contato com o autor (Priority: P3)

**Goal**: o recrutador encontra e aciona os links de LinkedIn, GitHub e e-mail (FR-007).

**Independent Test**: acionar cada link e confirmar o destino.

### Tests for User Story 5

- [x] T062 [P] [US5] Teste Playwright: os três links de contato levam ao destino correto, em `frontend/tests/e2e/contact.spec.ts` (mobile e desktop cobertos pelos projetos de `T022a`)

### Implementation for User Story 5

- [x] T063 [US5] Criar o componente `Contact` em `frontend/components/sections/Contact.tsx` (LinkedIn, GitHub, e-mail; sem formulário, conforme clarificação da spec)
- [x] T064 [US5] Adicionar a seção `Contact` a `frontend/app/[locale]/page.tsx` (depende de T028; alvo do botão "Falar comigo" de T026)

**Checkpoint**: todas as histórias de usuário funcionam de forma independente.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: qualidade, automação e validação final, cobrindo os critérios de sucesso restantes

- [x] T065 [P] Corrigir achados de acessibilidade (contraste, foco de teclado, `alt`) apontados pelo axe (depende de T022b e das checagens já incluídas em T023, T029, T058, T062) em todas as seções (FR-011)
- [x] T066 [P] Configurar Lighthouse CI (`frontend/lighthouserc.js`) com meta > 90 em desempenho, acessibilidade e SEO (SC-004)
- [x] T067 Criar `.github/workflows/health-check.yml`: agendado (`schedule`) + `workflow_dispatch`, chama `GET /health` em produção, falha explicitamente se não houver 200 (substitui o "ping do Space" do brief; ver plan.md nota N1)
- [x] T068 [P] Criar `.github/workflows/frontend-ci.yml`: lint, `tsc`, testes (Vitest + Playwright), build e Lighthouse CI, com `permissions:` mínimas
- [x] T069 [P] Criar `.github/workflows/backend-ci.yml`: `ruff check`, `pytest` (unit + contract + eval), com `permissions:` mínimas
- [x] T070 Criar `.github/workflows/ingest.yml`: gatilho por `paths: frontend/content/**`, roda `backend/scripts/ingest.py` e falha se `backend/data/kb/` ficar desatualizado em relação ao conteúdo
- [x] T071 Documentar em `README.md` a exigência de CI verde antes do merge na `main` (proteção de branch é configurada no GitHub, fora do código) e o resumo da arquitetura, com link para `specs/001-portfolio-portal/`
- [x] T072 Executar a validação ponta a ponta de [quickstart.md](quickstart.md) (os 10 cenários) e registrar o resultado
- [x] T073 [P] Revisar `backend/.env.example` e o `.gitignore` para confirmar que nenhuma credencial real foi commitada (constituição IX)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup — BLOQUEIA todas as histórias
- **User Stories (Phase 3–7)**: todas dependem da Fase 2 completa
  - US1 e US2 (P1) não dependem uma da outra
  - US3 (P2, chat) não depende de US1/US2, mas compartilha `page.tsx` (T034, T057) e o alvo de contato de US5 (T026 → T064)
  - US4 (P2) depende de US3 para o idioma do chat (T061 depende de T054)
  - US5 (P3) é independente, exceto pelo botão "Falar comigo" de US1 (T026) que aponta para ela
- **Polish (Phase 8)**: depende das histórias que forem entregues

### User Story Dependencies

- **US1 (P1)**: nenhuma dependência de outra história
- **US2 (P1)**: nenhuma dependência de outra história
- **US3 (P2)**: nenhuma dependência funcional; integra-se em `page.tsx`
- **US4 (P2)**: integra-se com US3 (idioma do chat) e com o conteúdo/CV das demais
- **US5 (P3)**: nenhuma dependência funcional; é o alvo do botão de US1

### Parallel Opportunities

- Setup: T002–T005 em paralelo
- Foundational: T009–T011a, T014–T018, T021–T022b em paralelo
- Dentro de cada história, as tarefas marcadas `[P]` (testes e componentes de arquivos distintos)
- Depois da Fase 2, US1, US2 e US5 podem avançar em paralelo; US3 pode começar em paralelo e US4 só fecha depois de T054 (US3)

---

## Parallel Example: User Story 3

```bash
# Testes de US3 em paralelo:
Task: "Testes unitários do VectorStore em backend/tests/unit/test_vector_store.py"
Task: "Testes unitários do InputGuard em backend/tests/unit/test_input_guard.py"
Task: "Testes unitários de limites em backend/tests/unit/test_limits.py"
Task: "Teste de contrato de /api/chat e /api/health em backend/tests/contract/test_chat_api.py"

# Implementações independentes de US3 em paralelo:
Task: "Implementar GeminiLLMClient em backend/app/llm/gemini.py"
Task: "Implementar FileVectorStore em backend/app/retrieval/file_store.py"
Task: "Implementar GroqPromptGuard em backend/app/guard/prompt_guard.py"
Task: "Implementar rate limiter no Upstash Redis em backend/app/limits/rate_limit.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 apenas)

1. Completar a Fase 1: Setup
2. Completar a Fase 2: Foundational (crítico — bloqueia tudo)
3. Completar a Fase 3: User Story 1
4. **PARAR e VALIDAR**: testar a US1 isoladamente (T023)
5. Publicar na Vercel se estiver pronto — já é um portfólio funcional, sem chat

### Incremental Delivery

1. Setup + Foundational → fundação pronta
2. US1 → validar → publicar (MVP)
3. US2 → validar → publicar (portfólio completo, sem IA)
4. US3 → validar → publicar (diferencial de IA no ar)
5. US4 → validar → publicar (alcance bilíngue e conforto)
6. US5 → validar → publicar (fecha o funil de contato)
7. Polish → CI/CD, acessibilidade, Lighthouse, validação final

Cada etapa é publicável e agrega valor sem quebrar a anterior.

## Notes

- `[P]` = arquivos diferentes, sem dependência pendente
- Cada história é entregável e testável de forma independente
- Fazer commit após cada tarefa ou grupo lógico, em um PR por história, com CI verde antes do merge na `main` (constituição VII)
- Evitar: tarefas vagas, conflito no mesmo arquivo, dependências entre histórias que quebrem a independência
