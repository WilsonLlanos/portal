<!-- Este arquivo alimenta a base de conhecimento do chat (ingest.py); não é exibido na página.
     Guarda os detalhes que a trajetória da página mostra só em resumo. -->

# CV — Wilson Llanos (PT-BR)

## Trajetória

Wilson é Desenvolvedor de Sistemas na EISA - Empresa Interagrícola e constrói soluções de IA
generativa em produção no ecossistema Azure, com foco em segurança e governança de dados. Já
desenvolveu um sistema multiagente com LangGraph e MCP para a triagem de incidentes de TI e,
atualmente, desenvolve um sistema multiagente com RAG híbrido para automatizar o suporte N1 de uma
plataforma de logística de café. Também atua na integração de dados entre quatro sistemas,
incluindo legados, eliminando erros recorrentes, e tem projetos de Machine Learning com Apache
Spark no Databricks.

Além disso, este próprio portal é outro exemplo de projeto relevante: ele disponibiliza um agente
de IA que ajuda o visitante a tirar dúvidas sobre a carreira de Wilson e destaca informações
relevantes que o visitante compartilhar na conversa.

## Projetos principais

### Sistema multiagente para incidentes de TI (concluído, 2026)
Python, LangGraph, MCP, Azure AI Foundry, Azure AI Search, Azure SQL. Wilson desenvolveu um sistema
multiagente focado na triagem automática de incidentes de TI e na redução do tempo de resposta
(MTTR). Implementou a orquestração de rotas assíncronas e o controle de estados com LangGraph, com
comunicação segura pelo padrão MCP (Model Context Protocol). Conectou o raciocínio do Azure AI
Foundry ao contexto operacional via RAG com Azure AI Search, usando Azure SQL para persistência de
memória e auditoria. Adotou Spec-Driven Development (SDD) para governar o comportamento dos agentes,
com contratos explícitos de ferramentas e aprovação humana em camadas para restringir o escopo dos
agentes e mitigar riscos de execução sem supervisão.

### RAG híbrido multiagente para automação do suporte N1 (em andamento, 2026)
LangGraph, Azure AI Foundry, Azure AI Search, Azure SQL. Sistema multiagente com RAG híbrido para
automatizar o suporte N1 de uma plataforma de logística de café, combinando busca vetorial (Azure AI
Search) e consultas ao banco relacional (Azure SQL) via Tool Calling, com raciocínio no Azure AI
Foundry. Inclui camada de governança e segurança com Microsoft Presidio para anonimização dinâmica
de dados pessoais (LGPD), além de telemetria e rastreamento de custos (FinOps) no Azure Application
Insights.

### Portal de Portfólio com Chat de IA (pessoal, código aberto)
Repositório: github.com/WilsonLlanos/portal. É este próprio site: um portfólio bilíngue (PT/EN) com
um assistente de IA que responde sobre a carreira de Wilson usando RAG sobre o currículo dele.
Frontend em Next.js e TypeScript; backend em FastAPI com Gemini; busca vetorial com embeddings
pré-calculados; guardrail Llama Prompt Guard 2 contra prompt injection, com degradação segura;
limite de perguntas por visitante e teto diário de custo no Upstash Redis; CI/CD com GitHub Actions
e deploy na Vercel. Foi desenvolvido com Spec-Driven Development (Spec Kit).

### Suporte multiagente para lojistas — case Getnet (desafio técnico, código aberto)
Repositório: github.com/WilsonLlanos/getnet-multi-agent-support-system. Desenvolvido como desafio
técnico de um processo seletivo: um serviço de suporte para lojistas de maquininhas Getnet com um
único endpoint, em que um roteador em LangGraph classifica cada mensagem e a envia a agentes
especializados. O agente de conhecimento faz RAG sobre fontes aprovadas (Chroma com embeddings
multilíngues locais) e consulta APIs externas (cotação PTAX do Banco Central e clima); o agente de
suporte responde com os dados do próprio lojista por meio de tools; um agente de escalonamento
registra o encaminhamento para atendimento humano. Há guardrails com motivos padronizados,
redação de dados pessoais, verificação de prompt injection e observabilidade com logs
estruturados. Quando o contexto é insuficiente, o sistema admite a limitação em vez de inventar.
Tecnologias: Python, FastAPI, LangGraph, LangChain, Claude, Chroma, Sentence Transformers, Docker.
Também foi desenvolvido com Spec-Driven Development.

### Avaliação de qualidade de retrieval (usada na EISA, código aberto)
Repositório: github.com/WilsonLlanos/rag-doc-quality. Ferramenta de linha de comando criada para o
projeto de RAG do suporte N1 da EISA: indexa o corpus de documentação e mede a qualidade da busca
antes de publicá-lo no Azure AI Search. Compara busca vetorial e híbrida (vetorial + BM25,
fundidas por RRF), roda um golden set de perguntas com as métricas Recall@k e MRR, compara com um
baseline salvo e lista as perguntas que falharam. Tecnologias: Python, Azure OpenAI (embeddings),
Qdrant, fastembed (BM25) e Typer.

## Progressão na EISA - Empresa Interagrícola

Wilson construiu sua carreira de tecnologia na EISA com promoções sucessivas.

### Desenvolvedor de Sistemas (desde jan/2026)
- Desenvolvendo solução de IA com sistema multiagente (LangGraph) e RAG híbrido no Azure para
  automatizar o suporte N1 de uma plataforma de logística de café.
- Desenvolveu comunicação orientada a eventos (Azure Service Bus + .NET), aprimorando o
  monitoramento das integrações.
- Gerencia integrações críticas entre o ERP e os sistemas logísticos, sincronizando mais de 50 mil
  registros por dia com 99,9% de precisão.
- Otimizou um pipeline ETL com SSIS, reduzindo drasticamente o tempo de processamento.
- Implementou fluxos bidirecionais para a migração de mais de 70 processos com zero downtime.

### Analista Programador (fev/2025 a dez/2025)
- Desenvolveu processos ETL (Azure Functions, SSIS) processando mais de 1 milhão de registros por
  mês com 99,8% de precisão.
- Criou relatórios analíticos (Reporting Services, Crystal Reports) para todo o processo logístico
  da commodity.
- Iniciou os primeiros protótipos de IA generativa com RAG e LLMs.
- Foi promovido a Desenvolvedor de Sistemas após superar metas, concluindo entregas antecipadamente.

### Analista de Suporte (abr/2022 a jan/2025)
- Prestou suporte técnico a usuários, diagnosticando e resolvendo problemas de sistemas, banco de
  dados e infraestrutura, reduzindo tickets recorrentes.

## Formação e certificações

O curso "Pipeline ETL e Machine Learning com Apache Spark", da Data Science Academy
(concluído em janeiro de 2025), foi o ponto de partida de Wilson no universo da IA.

Wilson concluiu o MBA em Inteligência Artificial e Big Data pelo ICMC/USP (2025-2026,
concluído em outubro de 2026) e é bacharel em Engenharia Civil pela Uninove (2012-2016). Tem as
certificações Microsoft Certified: Azure Data Fundamentals (DP-900) e "Pipeline ETL e Machine
Learning com Apache Spark", pela Data Science Academy.

## Filosofia de trabalho

"A questão não é desenvolver, mas sim, desenvolver e manter com eficiência e segurança, pensando
o melhor para cada projeto. E é exatamente isso que adoto em minhas soluções. Em um projeto mais
recente, onde estou implementando uma solução de suporte automatizado para usuários de um sistema
complexo em ambiente Azure, onde haverá uma integração do LLM com dois tipos de bancos diferentes
(vetorial e relacional), um desafio de engenharia que foi superado."


## Fora do trabalho (interesses pessoais)

Nas horas vagas, Wilson toca violão, joga Counter-Strike e acompanha as notícias sobre IA. Também
medita, o que o ajuda a manter o foco. Gosta de se manter atualizado testando novas tecnologias e,
de tempos em tempos, revisita os fundamentos da área para manter a eficiência na linha de frente.
