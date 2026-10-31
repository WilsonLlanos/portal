# Portal de Portfólio Profissional (IA)

Portal bilíngue (PT-BR/EN) para apresentar a carreira do autor a recrutadores,
com foco em IA, e um chat de IA (RAG) sobre essa carreira.

Este projeto foi desenvolvido com [Spec Kit](https://github.com/github/spec-kit):
veja [brief.md](brief.md) para o contexto e decisões de produto, e
[specs/001-portfolio-portal/](specs/001-portfolio-portal/) para a especificação
completa (`spec.md`), o plano técnico (`plan.md`, `research.md`,
`data-model.md`, `contracts/`) e as tarefas (`tasks.md`). Os princípios do
projeto (veracidade, custo mínimo, segurança em camadas, privacidade, CI/CD,
gestão de credenciais) estão em [.specify/memory/constitution.md](.specify/memory/constitution.md).

## Arquitetura

- **`frontend/`** — Next.js 16 (App Router, TypeScript, Tailwind CSS 4,
  `next-intl`, `next-themes`). Conteúdo estático em `frontend/content/`.
- **`backend/`** — FastAPI (Python 3.12, gerenciado com `uv`). Pipeline do
  chat: validação → teto diário → rate limit → guardrail (Prompt Guard 2 via
  Groq) → busca vetorial (arquivo + NumPy) → geração (Gemini) → observabilidade
  (Langfuse). Ver `specs/001-portfolio-portal/contracts/provider-interfaces.md`
  para as interfaces que tornam cada provedor substituível.
- Os dois projetos são implantados separadamente na Vercel; o frontend chama
  o backend via rewrite em `/api/*` (sem CORS em produção).

## Rodando localmente

Ver [specs/001-portfolio-portal/quickstart.md](specs/001-portfolio-portal/quickstart.md)
para o guia completo de validação. Resumo:

```powershell
# backend
cd backend
uv sync
uv run python scripts/ingest.py   # gera backend/data/kb/ a partir de frontend/content
uv run uvicorn app.main:app --reload --port 8000 # http://localhost:8000

# frontend (outro terminal)
cd frontend
npm ci
npm run dev                       # http://localhost:3000
```

Copie `backend/.env.example` para `backend/.env` e preencha com suas chaves
(nunca versione o `.env`).

## Pré-requisitos de conta (fora do código)

Antes do chat funcionar em produção, configure manualmente (ver
`specs/001-portfolio-portal/tasks.md` T007a/T007b e `plan.md` decisões O1/O2):

- [x] Teto de orçamento configurado no Google Cloud/AI Studio (`GEMINI_API_KEY`)
- [x] `GROQ_API_KEY` criada na camada gratuita da Groq, com acesso ao
      `meta-llama/llama-prompt-guard-2-86m` confirmado (sem cartão)

## Qualidade e CI/CD

Toda mudança passa por CI antes de entrar na `main` (constituição, Princípio
VII), e a `main` deve ser protegida no GitHub (**Settings → Branches → Branch
protection rules**, exigindo os checks `Frontend CI` e `Backend CI` antes do
merge — configuração do GitHub, não código). Workflows em
[.github/workflows/](.github/workflows/):

| Workflow | O que faz |
|---|---|
| `health-check.yml` | Verifica `GET /health` do backend em produção, agendado |
| `frontend-ci.yml` | Lint, typecheck, testes (Vitest + Playwright), build, Lighthouse CI |
| `backend-ci.yml` | `ruff` e `pytest` (sem os testes de `tests/eval`, que exigem credenciais reais) |
| `ingest.yml` | Confere (`ingest.py --check`) se `backend/data/kb/` está em dia com `frontend/content/`; a regeneração é feita localmente com `uv run python scripts/ingest.py` |

**Avaliação (`backend/tests/eval`) fora do CI, de propósito.** Os conjuntos de
perguntas e ataques de referência (SC-003, SC-007) fazem chamadas reais ao
Gemini e à Groq: exigem chaves e têm custo. Por isso o `backend-ci.yml` roda
`pytest --ignore=tests/eval`, divergindo da tarefa T069 ("unit + contract +
eval"). Rode a avaliação localmente antes de mudanças no prompt, no conteúdo ou
na busca, com `GEMINI_API_KEY` e `GROQ_API_KEY` no ambiente:

```bash
cd backend
uv run pytest tests/eval -s
```

## Conteúdo

O conteúdo do autor (`frontend/content/`) está **provisório** — veja os
comentários `_placeholder`/`[PLACEHOLDER]` nos arquivos JSON. Substituir pelo
conteúdo real (bio, experiências, projetos, certificações) antes de publicar.
A foto e os dois CVs reais já estão em `frontend/public/images/` e
`frontend/public/cv/`.
