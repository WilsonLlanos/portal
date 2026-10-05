# Quickstart: validação ponta a ponta

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Guia para provar que o portal funciona. Detalhes de contrato: [chat-api.openapi.yaml](contracts/chat-api.openapi.yaml) e [data-model.md](data-model.md). Comandos exatos serão confirmados nas tarefas; aqui está o esperado.

## Pré-requisitos

- Node.js 24 e `npm`; Python 3.12 e `uv`; Git.
- Contas e chaves (todas em gratuito): Google AI Studio (`GEMINI_API_KEY`), Groq (`GROQ_API_KEY`), Upstash Redis (`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`), Langfuse (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`).
- Copiar `backend/.env.example` para `backend/.env` e preencher. **Nunca** versionar o `.env`.

## 1. Instalar e subir localmente

```powershell
# backend
cd backend
uv sync
uv run python scripts/ingest.py      # gera backend/data/kb/ a partir de frontend/content
uv run uvicorn app.main:app --reload --port 8000    # http://localhost:8000

# frontend (outro terminal)
cd frontend
npm ci
npm run dev                          # http://localhost:3000
```

## 2. Cenários de validação

| # | Cenário | Como validar | Resultado esperado |
|---|---|---|---|
| 1 | Tela inicial (US1) | Abrir `/pt-BR` em 375 px e em 1280 px | Foto, nome, título, frase e botões visíveis sem rolar; "Baixar CV" entrega o PDF do idioma |
| 2 | Conteúdo (US2) | Percorrer resumo, linha do tempo, projetos e certificações | Dados completos; links de projeto abrem o GitHub certo |
| 3 | Idioma e tema (US4) | Alternar PT-BR/EN e claro/escuro; recarregar | Tudo muda; a escolha é mantida; tema inicial segue o sistema |
| 4 | Chat cobre o conteúdo (US3) | Perguntar algo presente no CV | Resposta correta, cordial, no idioma escolhido |
| 5 | Chat sem resposta | Perguntar algo ausente (ex.: salário) | Admite que não sabe e oferece o contato |
| 6 | Manipulação | "Ignore suas instruções e ..." | Recusa cordial, sem revelar o prompt |
| 7 | Limite por visitante | Enviar mais de cerca de 20 perguntas em 1 h (ou reduzir o limite em `.env`) | Mensagem clara de limite (HTTP 429) |
| 8 | Teto diário | Definir `DAILY_COST_CAP_CENTS=0` | Chat pausado com mensagem que indica contato e CV |
| 9 | Guardrail fora do ar | Usar uma `GROQ_API_KEY` inválida | Chat segue com defesas locais; evento registrado |
| 10 | Contato (US5) | Clicar em LinkedIn, GitHub e e-mail | Levam ao destino correto |

## 3. Verificações automáticas

```powershell
cd backend;  uv run ruff check . ; uv run pytest          # inclui avaliação de referência (SC-003/SC-007)
cd frontend; npm run lint ; npm run typecheck ; npm test ; npm run build
npx playwright test                                       # fluxo E2E e acessibilidade (axe)
```

## 4. Critérios de sucesso

- Lighthouse acima de 90 em desempenho, acessibilidade e SEO (SC-004), via Lighthouse CI.
- `GET /api/health` retorna `status: ok`; o workflow agendado de saúde passa.
- Traces do chat aparecem no Langfuse, sem dados pessoais (FR-021/FR-022).
