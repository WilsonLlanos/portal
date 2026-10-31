# Portal de Portfólio com Chat de IA — como funciona

## Visão geral do Portal
O Portal é o site de portfólio do Wilson Llanos: um site bilíngue (português e inglês) com um assistente de IA que responde perguntas sobre a carreira dele. O assistente usa RAG (Retrieval-Augmented Generation) sobre o próprio conteúdo do portfólio: currículo, experiências, projetos, certificações e esta descrição técnica do site. O código é aberto (github.com/WilsonLlanos/portal) e foi desenvolvido com Spec-Driven Development.

## Arquitetura e stack do Portal
O frontend usa Next.js 16 (App Router), TypeScript, Tailwind CSS 4, next-intl para as rotas /pt-BR e /en e next-themes para os temas claro e escuro. As páginas são pré-renderizadas em build (SSG). O backend é Python 3.12 com FastAPI, gerenciado com uv. Frontend e backend são publicados como dois projetos separados na Vercel. O chat responde por streaming (Server-Sent Events). O conteúdo fica em arquivos versionados em frontend/content/, e a mesma fonte alimenta as páginas e a base de conhecimento do chat, para o que o site mostra e o que o chat sabe não divergirem.

## Pipeline do chat, passo a passo
Cada pergunta passa por estas etapas, nesta ordem: (1) validação do tamanho da mensagem (até 500 caracteres); (2) verificação do teto diário de custo; (3) rate limit por visitante; (4) guardrail contra prompt injection (InputGuard); (5) recuperação dos trechos relevantes na base de conhecimento (RAG); (6) montagem do prompt com o contexto recuperado e o histórico curto da conversa; (7) geração da resposta pelo LLM, em streaming; (8) registro da interação para observabilidade. O servidor não guarda estado da conversa: o cliente envia as últimas 4 mensagens junto com a pergunta.

## RAG: ingestão e base de conhecimento
A base de conhecimento é gerada pelo script backend/scripts/ingest.py. Ele lê o conteúdo de frontend/content/ nos dois idiomas, quebra o texto em trechos (chunks) de cerca de 180 palavras, ou por seção no caso desta descrição técnica, e gera um embedding para cada trecho com o modelo gemini-embedding-001 do Google. O resultado é gravado em arquivos em backend/data/kb/: chunks.json (texto e metadados, como idioma e origem), vectors.npz (matriz de embeddings) e manifest.json (modelo, dimensão, data e um hash do conteúdo). Um check no GitHub Actions compara esse hash com o conteúdo atual e bloqueia o merge se a base estiver desatualizada.

## RAG: busca vetorial sem banco vetorial
O Portal não usa banco vetorial. Como a base é pequena, a busca é feita em memória com NumPy, por similaridade de cosseno, atrás de uma interface VectorStore (FileVectorStore) que permite trocar por um banco vetorial, como o Qdrant, no futuro. Na pergunta, o backend gera o embedding da mensagem com o mesmo modelo, filtra os trechos pelo idioma da sessão, calcula o cosseno contra todos de uma vez (multiplicação de matriz) e envia ao LLM os 5 mais parecidos (top_k = 5). Ao iniciar, o backend confere se o modelo de embedding do manifest é o mesmo configurado, para não comparar vetores incompatíveis. Alternativas consideradas e descartadas: Qdrant Cloud (suspende por inatividade), Chroma (persistência em disco não funciona em serverless) e pgvector (excessivo para o volume).

## Geração da resposta (LLM)
As respostas são geradas pelo Google Gemini, via SDK google-genai, atrás de uma interface LLMClient que permite trocar de provedor por configuração. A temperatura é 0,4 e o limite é de 512 tokens de saída por resposta. O prompt de sistema exige responder apenas com base no contexto recuperado, admitir quando não sabe e responder no idioma em que o visitante escreveu. O Portal usa a camada paga do Gemini, com orçamento limitado, porque na camada gratuita o Google pode usar o conteúdo enviado para melhorar seus produtos.

## Segurança: guardrail contra prompt injection
Antes de qualquer busca, a pergunta passa pelo Llama Prompt Guard 2 (86M), um classificador de prompt injection da Meta, chamado via API da Groq. Ele devolve uma probabilidade de ataque, e o backend bloqueia a pergunta a partir de 0,5, respondendo com uma recusa educada. Há também heurísticas locais com expressões regulares, em português e inglês. A política é fail-open com degradação: se a Groq ficar lenta (timeout de 2 segundos) ou fora do ar, um circuit breaker para de chamá-la por 60 segundos após 3 falhas seguidas, e o chat continua funcionando apenas com as defesas locais.

## Limites de custo e rate limit
Para controlar custo e abuso, o Portal limita cada visitante a 20 perguntas por hora e tem um teto diário de custo estimado de 50 centavos de dólar. Ao atingir o teto, o chat é pausado até o dia seguinte. Os contadores ficam no Upstash Redis, porque funções serverless não compartilham memória. O visitante é identificado por um hash do IP e do user agent com sal diário, sem guardar o IP. Se o Redis falhar, entra um limitador em memória mais restritivo (10 perguntas por hora): para custo, a política é fail-safe.

## Observabilidade, testes e CI/CD
Cada interação do chat é registrada no Langfuse Cloud (idioma, resultado — respondida, recusada, sem resposta ou erro —, resultado do guardrail, IDs dos trechos recuperados, tokens e custo estimado, sem dados pessoais do visitante), além de logs JSON estruturados e um endpoint GET /health. Os testes usam pytest e ruff no backend, e Vitest, ESLint, Playwright (com checagem de acessibilidade) e Lighthouse CI no frontend. Há também conjuntos de avaliação com perguntas e ataques reais. O GitHub Actions roda o CI do backend, o CI do frontend, o check de base de conhecimento em dia e um health check agendado da produção a cada 30 minutos. A branch main é protegida e só recebe código por pull request com os checks verdes. O deploy é feito pela integração nativa da Vercel.

## Spec-Driven Development
O Portal foi construído com Spec-Driven Development (Spec Kit): primeiro uma constituição com os princípios do projeto, depois a especificação (spec.md), a pesquisa com as decisões técnicas (research.md), o plano (plan.md), o modelo de dados e a lista de tarefas (tasks.md), e só então a implementação. Os artefatos ficam em specs/001-portfolio-portal/ no repositório.
