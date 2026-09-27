# Data Model: Portal de Portfólio Profissional (IA)

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Não há banco de dados relacional. Os dados vivem em três lugares: **arquivos de conteúdo versionados** (fonte da verdade), **artefatos derivados** (base de conhecimento do chat) e **estado efêmero** (Redis e observabilidade).

## 1. Conteúdo do autor (arquivos versionados)

Local: `frontend/content/{pt-BR,en}/`. Cada idioma tem os mesmos arquivos e o mesmo esquema; a validação em CI garante que ambos os idiomas estejam completos (edge case "idioma sem tradução").

### Profile (`profile.json`)
| Campo | Tipo | Regra |
|---|---|---|
| `name` | string | obrigatório |
| `headline` | string | título profissional, obrigatório |
| `tagline` | string | frase de posicionamento, obrigatório |
| `summary` | string | resumo de carreira curto, foco em IA |
| `photo` | { `src`, `alt` } | `alt` obrigatório (acessibilidade) |
| `links` | { `linkedin`, `github`, `email` } | URLs/e-mail válidos; sem telefone nem endereço |

### Experience (`timeline.json`, lista)
| Campo | Tipo | Regra |
|---|---|---|
| `id` | string | único |
| `kind` | `"professional"` \| `"academic"` | obrigatório |
| `organization` | string | empresa ou instituição |
| `role` | string | cargo ou curso |
| `start` / `end` | `YYYY-MM` / `YYYY-MM` \| `null` | `end = null` significa em andamento; `start <= end` |
| `description` | string | descrição curta |
| `highlights` | string[] | resultados (base para o chat destacar pontos fortes, sem exagero) |

Ordenação: cronológica decrescente na exibição.

### Project (`projects.json`, lista)
| Campo | Tipo | Regra |
|---|---|---|
| `id` | string | único |
| `name` | string | obrigatório |
| `description` | string | obrigatório |
| `technologies` | string[] | pelo menos 1 |
| `repoUrl` | URL | repositório do GitHub |
| `demoUrl` | URL \| null | opcional |

### Certification (`certifications.json`, lista)
| Campo | Tipo | Regra |
|---|---|---|
| `id` | string | único |
| `name` | string | obrigatório |
| `issuer` | string | obrigatório |
| `date` | `YYYY-MM` | obrigatório |
| `verifyUrl` | URL \| null | opcional |

### CV
PDFs estáticos: `frontend/public/cv/cv-pt-BR.pdf` e `frontend/public/cv/cv-en.pdf` (um por idioma). Os textos do CV também entram na base de conhecimento (`frontend/content/{lang}/cv.md`).

### Textos de interface
`frontend/messages/{pt-BR,en}.json` (rótulos, botões, mensagens de erro e de limite do chat, aviso de privacidade).

## 2. Base de conhecimento do chat (artefato derivado)

Gerada por `backend/scripts/ingest.py` a partir do conteúdo acima. **Não editar à mão.** Versionada em `backend/data/kb/`.

### KnowledgeChunk
| Campo | Tipo | Regra |
|---|---|---|
| `id` | string | estável (ex.: `en:project:portal-ia:0`) |
| `lang` | `"pt-BR"` \| `"en"` | filtro de busca |
| `source` | `profile` \| `experience` \| `project` \| `certification` \| `cv` | origem, usada para citar/rastrear |
| `source_id` | string | id do item de origem |
| `text` | string | trecho, em torno de 150 a 300 tokens |
| `embedding` | float[] | vetor do trecho (arquivo `.npz`, alinhado por índice) |

Arquivos: `chunks.json` (metadados e texto), `vectors.npz` (matriz de embeddings), `manifest.json` (modelo de embedding, dimensão, data, hash do conteúdo). A busca só é válida se o `manifest` corresponder ao modelo configurado; caso contrário, o backend falha na inicialização (fail-fast).

## 3. Estado efêmero

### VisitorKey (Redis, TTL curto)
Chave = hash(IP + user agent + sal do dia); **nunca** o IP bruto. Guarda o contador de requisições (janela de 1 hora, limite de cerca de 20) com expiração automática.

### DailyCost (Redis, TTL de 48 h)
Chave = data (UTC). Acumula custo estimado em centavos a partir dos tokens usados. Ao atingir `DAILY_COST_CAP_CENTS`, o backend entra em **estado pausado** até a virada do dia (FR-024).

**Transições do chat**: `ativo` → (teto atingido) → `pausado até o dia seguinte` → (virada do dia) → `ativo`. Independentemente, o guardrail tem `normal` ↔ `degradado` (circuit breaker por falhas consecutivas do serviço de proteção).

### ChatRequest (em memória, por requisição; não persistido)
`message` (máx. em caracteres definido em configuração e no limite de contexto do guardrail), `lang`, `history` (até 4 trocas anteriores, validadas e truncadas no servidor).

### ChatInteraction (Langfuse, retenção de 30 dias)
| Campo | Regra |
|---|---|
| `question` | texto sanitizado; sem dados pessoais |
| `lang` | idioma da sessão |
| `retrieved_chunk_ids` | trechos usados |
| `guard_result` | `pass` \| `blocked` \| `skipped_degraded` + pontuação |
| `latency_ms`, `tokens_in`, `tokens_out`, `cost_estimate` | métricas |
| `outcome` | `answered` \| `no_answer` \| `refused` \| `rate_limited` \| `paused` \| `error` |

`outcome = no_answer` alimenta a lista de lacunas no conteúdo do autor. **Nunca** gravar IP, user agent bruto ou identificadores do visitante.
