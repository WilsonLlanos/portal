# Research: Portal de Portfólio Profissional (IA)

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-09-26

Pesquisa feita em 2026-09-26 na documentação oficial e em fontes secundárias. Valores de preço e cota mudam com frequência: os itens marcados com **(verificar)** devem ser reconfirmados na implementação.

## D1. Frontend: framework, estilo e i18n

- **Decision**: Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 + `next-intl` (rotas `/pt-BR` e `/en`) + `next-themes` (claro/escuro). Conteúdo estático gerado em build (SSG).
- **Rationale**: SEO e desempenho (Lighthouse > 90) exigem HTML pré-renderizado, e a Vercel é o alvo. O App Router é o padrão do Next.js 16, e o `next-intl` é a solução dominante de i18n nele. Tailwind acelera um visual moderno e temas claro/escuro. O autor quer aprender React: o Next.js tem a melhor documentação e a maior comunidade.
- **Alternatives considered**: Angular (mais pesado para site de conteúdo, SSR menos direto); Astro (excelente para conteúdo, mas o autor quer aprender React); Vite + React puro (sem SSG/SEO prontos).
- **Notas**: `next-intl` e o recurso `use cache` do Next.js 16 ainda não funcionam bem juntos; evitar `use cache` no MVP **(verificar)**.

## D2. Backend: linguagem e framework

- **Decision**: Python 3.12 + FastAPI, gerenciado com `uv`, implantado como projeto separado na Vercel (Root Directory `backend/`).
- **Rationale**: preferência do autor e ecossistema de IA em Python. A Vercel suporta FastAPI; o limite de pacote Python é **500 MB** descompactado, e a duração máxima na Hobby é 300 s com 2 GB de memória ([Vercel Functions Limits](https://vercel.com/docs/functions/limitations)). O corpo de requisição/resposta é limitado a 4,5 MB, o que basta para chat.
- **Alternatives considered**: C# (sem vantagem no ecossistema de IA); Next.js Route Handlers para o chat (ficaria em TypeScript, contrariando a preferência e o objetivo de mostrar Python/IA).
- **Nota de licença**: o plano Hobby da Vercel é para uso não comercial; um portfólio pessoal se enquadra.

## D3. LLM de geração

- **Decision**: Google Gemini via SDK `google-genai`, modelo `gemini-3.1-flash-lite` (configurável por variável de ambiente), atrás da interface `LLMClient`. Temperatura moderada (0,3 a 0,5), com o tom definido por prompt de sistema.
- **Rationale**: o autor já tem a chave. Flash-Lite tem camada gratuita, e o pago custa em torno de US$ 0,25 / US$ 1,50 por 1 M tokens de entrada/saída (3.1) **(verificar)**. Já existe o `gemini-3.5-flash-lite` (US$ 0,30 / US$ 2,50), mais caro; ficam trocáveis por configuração ([preços](https://ai.google.dev/gemini-api/docs/pricing)).
- **Risco de privacidade (importante)**: na camada **gratuita**, o Google informa que o conteúdo enviado **pode ser usado para melhorar seus produtos**; na paga, não. Ver decisão em aberto O1 no plano.
- **Prompt caching**: o *context caching* dos modelos Flash-Lite é oferecido apenas na camada paga, e o prefixo estável (instruções) do nosso prompt é pequeno. **Decisão: não usar caching no MVP.** Reavaliar somente se o prompt de sistema ficar grande.
- **Alternatives considered**: Groq para geração (modelos Llama 3.x saíram das camadas gratuita e Developer em 2026-08-16, e os modelos gratuitos atuais têm cotas baixas de tokens); manter como alternativa atrás da interface.

## D4. Embeddings e busca vetorial

- **Decision**: embeddings com o modelo Gemini Embedding (camada gratuita disponível; cerca de US$ 0,20 por 1 M tokens no pago **(verificar o ID exato do modelo)**), pré-calculados por um script de ingestão e gravados em arquivo (`backend/data/kb/`: vetores em `.npz` + metadados em JSON). A busca é feita com NumPy (similaridade de cosseno) atrás da interface `VectorStore`. A pergunta do visitante é embutida em tempo de requisição (uma chamada pequena).
- **Rationale**: a base tem dezenas a poucas centenas de trechos; um índice em arquivo é grátis, sem serviço externo, sem suspensão por inatividade e didático. O arquivo cabe folgadamente nos 500 MB da função.
- **Alternatives considered**: Qdrant Cloud (plano B pela interface, porém com suspensão por inatividade na camada gratuita); Chroma (persistência em disco não funciona em serverless); pgvector (excessivo).
- **Vetor por idioma**: cada trecho tem o metadado `lang`; a busca filtra pelo idioma da sessão e, se houver pouca cobertura, complementa com o outro idioma.

## D5. Guardrail de entrada (Prompt Guard 2)

- **Decision**: **Llama Prompt Guard 2 86M via API da Groq** (`meta-llama/llama-prompt-guard-2-86m`), atrás da interface `InputGuard`, complementada por defesas locais (limite de tamanho, heurísticas, rate limit, prompt de sistema restrito). Política **fail-open com degradação**: timeout curto (cerca de 2 s), circuit breaker em memória e, quando o guardrail estiver fora, defesas locais mais restritas + evento registrado.
- **Rationale**: o modelo tem 512 tokens de contexto e suporte multilíngue em 8 idiomas; na Groq custa cerca de US$ 0,04 por 25 M tokens ([Groq docs](https://console.groq.com/docs/model/meta-llama/llama-prompt-guard-2-86m)), praticamente zero para o volume do portfólio.
- **MUDANÇA EM RELAÇÃO AO BRIEF**: o brief previa hospedar o classificador em um **Space do Hugging Face**. A documentação atual informa que Spaces Docker/Gradio **exigem plano pago (PRO)** para serem criados ([Spaces Overview](https://huggingface.co/docs/hub/en/spaces-overview)); só Spaces estáticos são gratuitos. Isso derruba a opção (c) do brief. Consequência positiva: sem Space, **não há cold start nem necessidade de "ping" para mantê-lo acordado**.
- **Risco a verificar**: a documentação da Groq não confirma se o Prompt Guard 2 está incluído na camada gratuita (o catálogo de modelos gratuitos mudou em 2026-08). Se não estiver, o custo é de centavos com cartão. A política fail-open protege a experiência do visitante enquanto isso.
- **Alternative (plano B)**: Prompt Guard 2 (22M/86M) em ONNX quantizado dentro da função Python da Vercel, possível pelo limite de 500 MB (ou 5 GB em *large functions*, beta), porém com mais trabalho de conversão, licença Llama e cold start. Também: LLM pequeno como classificador.
- **Alternatives rejected**: Guardrails AI (foca validação de saída, dependências pesadas para serverless); Space pago no HF.

## D6. Estado compartilhado: rate limit, teto diário de custo, circuit breaker

- **Decision**: **Upstash Redis** (camada gratuita: 500 mil comandos por mês, 256 MB, via REST) para os contadores de rate limit por visitante, o acumulado diário de custo e o *kill switch* do teto. O circuit breaker do guardrail fica em memória por instância. Se o Redis falhar, aplicar um limitador em memória mais restritivo (fail-safe).
- **Rationale**: funções serverless não compartilham memória; sem um armazenamento compartilhado, rate limit e teto diário não são confiáveis. O uso previsto (poucos comandos por pergunta) cabe com folga nos 500 mil comandos mensais; uma requisição rejeitada também consome comando ([issue exemplo](https://github.com/KovalDenys1/Boardly/issues/1156)).
- **Identificação do visitante**: hash do IP + user agent com sal diário, sem armazenar IP bruto (privacidade).
- **Alternatives considered**: Vercel KV (é Upstash por trás); rate limit só em memória (inefetivo em serverless).

## D7. Observabilidade

- **Decision**: **Langfuse Cloud (Hobby)** para rastreamento do chat (pergunta, trechos recuperados, resultado do guardrail, tokens, custo, latência, erros), mais logs JSON estruturados nos logs da Vercel e um endpoint `GET /health`.
- **Rationale**: a camada Hobby dá 50 mil *units* por mês e **30 dias de retenção**, alinhada à retenção de 30 dias da spec (FR-022); o limite é rígido, sem cobrança extra ([fontes](https://dev.to/beton/langfuse-pricing-teardown-2026-2pi9)). Se a cota acabar, o rastreamento para, mas o chat segue (envio assíncrono, tolerante a falha).
- **Privacidade**: enviar apenas a pergunta já sanitizada (sem IP nem identificadores), com aviso ao visitante (FR-022).
- **Alternatives considered**: apenas logs JSON (sem painel, retenção curta da Vercel); LangSmith; OpenTelemetry autohospedado (excessivo).

## D8. Testes e qualidade

- **Decision**: backend com `pytest` + `ruff`; frontend com Vitest + Testing Library + ESLint + `tsc`; fluxo E2E mínimo com Playwright (inclui checagem de acessibilidade com axe); **Lighthouse CI** para SC-004.
- **Rationale**: a constituição (VIII) pede testes proporcionais na lógica crítica: busca, guardrails, política de falha, limites e teto de custo. Lighthouse CI dá uma métrica objetiva para o critério de sucesso e é um bom exercício de GitHub Actions.
- **Conjuntos de referência**: `backend/tests/eval/` terá perguntas de referência (SC-003) e ataques de referência (SC-007), em PT e EN.

## D9. CI/CD e automação (GitHub Actions)

- **Decision**: workflows pequenos, na ordem da constituição: (1) **verificação de saúde agendada** do backend em produção (`schedule` + `curl`, com falha explícita), que substitui o "ping do Space" do brief; (2) CI do frontend; (3) CI do backend; (4) regeneração de embeddings quando `frontend/content/**` mudar; (5) proteção da `main` exigindo CI verde; (6) Lighthouse CI em PRs. Deploy pela integração nativa da Vercel (sem pipeline próprio).
- **Rationale**: o objetivo de aprender Actions é mantido. Workflows agendados em repositórios públicos são desativados após cerca de 60 dias sem atividade, então o plano prevê um lembrete/alerta e o `workflow_dispatch` manual.
- **Segredos**: `GEMINI_API_KEY`, `GROQ_API_KEY`, `UPSTASH_REDIS_REST_URL/TOKEN`, `LANGFUSE_*` na Vercel; no GitHub Secrets apenas o que os workflows usam (chave do Gemini para a ingestão e URL de produção para a saúde). `permissions:` mínimas em todos os workflows.

## D10. Conteúdo, CV e foto

- **Decision**: conteúdo em arquivos versionados (`frontend/content/{pt-BR,en}/*.json`), com esquema tipado e validação em CI. A mesma fonte alimenta a página (SSG) e a ingestão da base de conhecimento. PDFs do CV em `frontend/public/cv/`; foto otimizada com `next/image`.
- **Rationale**: uma única fonte da verdade evita divergência entre o que o site mostra e o que o chat sabe (princípio I). Sem CMS nem banco (fora do escopo).
- **Cuidado**: o repositório será público; não colocar telefone, endereço nem documentos no conteúdo.

## D11. Memória curta e streaming do chat

- **Decision**: o cliente envia as últimas N=4 trocas junto com a pergunta; o servidor é sem estado, valida e trunca o histórico e aplica as mesmas proteções sobre ele. Respostas por *streaming* (Server-Sent Events).
- **Rationale**: cumpre FR-013a sem persistir conversas; o streaming melhora a percepção de velocidade.

## Resumo dos itens a verificar na implementação

1. Prompt Guard 2 na camada gratuita da Groq (ou custo com cartão).
2. ID exato e cota do modelo de embedding do Gemini.
3. Camada de cobrança do Gemini (gratuita vs paga) e privacidade (ver O1 no plano).
4. Compatibilidade `next-intl` + Next.js 16.
5. Estrutura de entrada do FastAPI na Vercel (`backend/`).
